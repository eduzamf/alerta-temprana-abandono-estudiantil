"""Audit historical LR OOF ranking without refitting or accessing test cases."""
import json
import math
from statistics import NormalDist

import numpy as np
import pandas as pd

from .data_processing import ROOT, load_development
from .eda import subgroup_series
from .verify import verify as verify_baselines


def wilson(successes, total):
    if total < 0 or successes < 0 or successes > total:
        raise ValueError("Invalid binomial counts")
    if total == 0:
        return None, None, None
    z = NormalDist().inv_cdf(.975)
    p = successes / total
    divisor = 1 + z*z/total
    center = (p + z*z/(2*total)) / divisor
    radius = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / divisor
    return p, max(0., center-radius), min(1., center+radius)


def counts(group):
    selected = group.selected_top20.to_numpy(dtype=bool)
    dropout = group.actual.eq("Dropout").to_numpy()
    predicted = group.predicted.eq("Dropout").to_numpy()
    return {
        "n": len(group), "selected": int(selected.sum()),
        "dropout": int(dropout.sum()), "non_dropout_at_cutoff": int((~dropout).sum()),
        "selected_dropout": int((selected & dropout).sum()),
        "selected_non_dropout": int((selected & ~dropout).sum()),
        "selected_enrolled": int((selected & group.actual.eq("Enrolled").to_numpy()).sum()),
        "selected_graduate": int((selected & group.actual.eq("Graduate").to_numpy()).sum()),
        "classifier_false_positive": int((predicted & ~dropout).sum()),
    }


RATES = {
    "selection_rate": ("selected", "n"),
    "dropout_coverage": ("selected_dropout", "dropout"),
    "ranking_fpr": ("selected_non_dropout", "non_dropout_at_cutoff"),
    "ranking_error_fraction": ("selected_non_dropout", "selected"),
    "classifier_fpr": ("classifier_false_positive", "non_dropout_at_cutoff"),
}


def audit_group(group, dimension, label):
    row = {"dimension": dimension, "group": str(label), **counts(group)}
    for name, (num, den) in RATES.items():
        rate, low, high = wilson(row[num], row[den])
        row[name] = rate
        row[name + "_low"] = low
        row[name + "_high"] = high
        row[name + "_denominator_under_30"] = row[den] < 30
    # Expected detections for uniform sampling of the same k within each fold.
    expected = float(group.loc[group.actual.eq("Dropout"), "random_probability"].sum())
    row["random_expected_detected"] = expected
    row["random_expected_coverage"] = expected / row["dropout"] if row["dropout"] else None
    return row


def compute():
    verify_baselines()
    frame, _ = load_development()
    predictions = pd.read_csv(ROOT / "results/metrics/baseline_predictions.csv", float_precision="round_trip")
    pred = predictions.loc[predictions.model.eq("LR_base")].set_index("row_index")
    np.testing.assert_array_equal(pred.index, frame.index)
    pred = pred.copy()
    pred["random_probability"] = pred.groupby("fold").selected_top20.transform("mean")
    rows = [audit_group(pred, "Total", "Todos")]
    for dimension, values in subgroup_series(frame).items():
        for label in values.dropna().unique():
            rows.append(audit_group(pred.loc[values.eq(label)], dimension, label))
    historical = json.loads((ROOT / "results/metrics/baseline_results.json").read_text())
    return {
        "model": "LR_base", "scope": "Historical out-of-fold development predictions",
        "test_scored": False, "rows": rows,
        "historical_mean_fold_coverage": historical["summary"]["LR_base"]["val_recall20"],
        "aggregation": "Pooled OOF counts; not unweighted fold means",
        "interval": "95% Wilson marginal binomial intervals; descriptive, not simultaneous; do not capture model training variability or fixed-quota dependence",
    }


def format_rate(row, name):
    if row[name] is None:
        return "No estimable"
    return f"{100*row[name]:.2f}% [{100*row[name+'_low']:.2f}; {100*row[name+'_high']:.2f}]"


def render(report):
    total = report["rows"][0]
    lookup = {(r["dimension"], r["group"]): r for r in report["rows"]}
    young = lookup[("Edad", "Menos de 20")]
    older = lookup[("Edad", "35 o mas")]
    special = lookup[("Necesidades especiales (codigo)", "1")]
    tables = []
    for dimension in dict.fromkeys(r["dimension"] for r in report["rows"]):
        subset = [r for r in report["rows"] if r["dimension"] == dimension]
        table = [f"## {dimension}", "",
                 "| Grupo/codigo | n | Priorizados | Abandonos detectados / reales | Seleccion [IC95%] | Cobertura [IC95%] | FPR ranking [IC95%] |",
                 "|---|---:|---:|---:|---|---|---|"]
        for row in subset:
            table.append(f"| {row['group']} | {row['n']} | {row['selected']} | {row['selected_dropout']}/{row['dropout']} | {format_rate(row, 'selection_rate')} | {format_rate(row, 'dropout_coverage')} | {format_rate(row, 'ranking_fpr')} |")
        tables.append("\n".join(table))
    return f"""# Auditoria por subgrupos de la regresion de referencia

## Alcance

Se audita LR_base, el mismo procedimiento de regresion logistica de las entregas
anteriores. Se reutilizan sus 3.539 predicciones fuera de entrenamiento (OOF)
verificadas, sin reentrenar ni cambiar el ranking. Esta auditoria no selecciona
un modelo final. La reserva de 885 casos no participa.

La seleccion conserva el 20% redondeado hacia arriba dentro de cada fold,
no el 20% de cada subgrupo. Edad conserva los intervalos del EDA. Nacionalidad
mantiene cada codigo, sin fusionar grupos despues de observar sus resultados.
Beca y deuda son atributos de auditoria retrospectiva, no predictores.

## Definiciones

- Tasa de seleccion: priorizados / total del grupo.
- Cobertura: abandonos priorizados / abandonos reales del grupo.
- FPR del ranking: priorizados sin abandono registrado / casos sin abandono registrado.
- Fraccion de error de la lista: priorizados sin abandono registrado / priorizados.
- FPR del clasificador: predicciones de clase Dropout incorrectas / casos sin abandono registrado.

Los dos ultimos indicadores y todos los conteos se incluyen en el CSV.
FPR del ranking y del clasificador son decisiones diferentes. Enrolled se
considera no abandono **al corte del dataset**, no exito definitivo; por eso
se separan los seleccionados Enrolled y Graduate. No se interpreta priorizar
a un estudiante Enrolled como una ayuda necesariamente innecesaria.

## Resultado global y comparacion aleatoria

Se priorizan {total['selected']} de {total['n']} estudiantes y se detectan
{total['selected_dropout']} de {total['dropout']} abandonos: cobertura agrupada
**{100*total['dropout_coverage']:.4f}%**. El {100*report['historical_mean_fold_coverage']:.4f}%
publicado anteriormente es la **media no ponderada de cinco folds**. Son
agregaciones distintas de las mismas predicciones, no resultados contradictorios.

Un ranking uniforme aleatorio con el mismo cupo por fold detectaria en esperanza
{total['random_expected_detected']:.2f} abandonos, cobertura
{100*total['random_expected_coverage']:.4f}%. La cobertura observada equivale a
{total['dropout_coverage']/total['random_expected_coverage']:.2f} veces esa esperanza.
Esto no es una prueba de significacion ni evidencia de reduccion causal del abandono.

## Como interpretar los intervalos

Se presentan intervalos marginales de Wilson al 95%, calculados con el numerador
y denominador propios de cada tasa. Un denominador cero es **no estimable**, no
0%. El CSV marca denominadores menores de 30 como advertencia descriptiva, no
como un umbral de significacion. No se publican filas individuales nuevas.

Estos intervalos binomiales son aproximaciones descriptivas: el cupo fijo induce
dependencia y los modelos de los folds comparten entrenamiento. No incorporan
la variabilidad del ajuste ni corrigen comparaciones multiples. Su solapamiento
no prueba igualdad y su separacion no demuestra discriminacion causal.

## Hallazgos que requieren revision

La cobertura en menores de 20 anos es {format_rate(young, 'dropout_coverage')},
frente a {format_rate(older, 'dropout_coverage')} en estudiantes de 35 o mas.
El sistema deja fuera a {young['dropout']-young['selected_dropout']} de los
{young['dropout']} abandonos del grupo mas joven. La mayor cobertura del grupo
de mayor edad viene acompanada de una FPR del ranking de
{format_rate(older, 'ranking_fpr')}; detectar mas no implica ausencia de errores.

En necesidades especiales, codigo 1, solo hay {special['n']} casos y
{special['dropout']} abandonos. Se detectan {special['selected_dropout']},
con cobertura {format_rate(special, 'dropout_coverage')}. La incertidumbre impide
extraer conclusiones firmes sobre este grupo. Las tablas de genero y beca
tambien muestran coberturas distintas; merecen seguimiento, no una declaracion
automatica de equidad. Beca no interviene como predictor en este modelo.

{(chr(10)*2).join(tables)}

## Uso responsable de los resultados

Una tasa de seleccion distinta no basta para afirmar trato injusto: se debe
considerar prevalencia, cobertura, errores, tamano del grupo y contexto. Los
grupos pequenos requieren especial cautela; cero detecciones no significa
ausencia de riesgo. No se deben fijar cuotas ni excluir grupos a partir de
estas tablas. Los codigos conservan la nomenclatura del dataset original.

El resultado respalda revisar el prototipo antes de cualquier uso institucional,
mantener revision humana y ofrecer acceso voluntario al apoyo fuera del ranking.
No demuestra equidad, eficacia de una intervencion ni validez en Ecuador.

## Reproduccion

Ejecutar `python -m src.fairness`. [Conteos y tasas](../metrics/fairness_subgroups.csv)
y [evidencia JSON](../metrics/fairness_results.json) se generan desde las mismas
predicciones verificadas. El procedimiento conserva el modelo y los resultados
historicos; no modifica hiperparametros a partir de la auditoria.
"""


def run():
    report = compute()
    (ROOT / "results/metrics/fairness_results.json").write_text(
        json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    pd.DataFrame(report["rows"]).to_csv(ROOT / "results/metrics/fairness_subgroups.csv", index=False)
    (ROOT / "results/reports/fairness_report.md").write_text(render(report), encoding="utf-8")
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps(result["rows"][0], indent=2))
