"""Report nested results and descriptive sensitivity of the RF search surface."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.inspection import PartialDependenceDisplay

from .data_processing import ROOT
from .optimize import STRATEGIES, verify

PARAMS = ["n_estimators", "max_depth", "min_samples_leaf"]
FIGURES = [
    "optimization_01_comparison.png", "optimization_02_pdp.png",
    "optimization_03_importance.png", "optimization_04_interaction.png",
    "optimization_05_lr.png",
]


def save(fig, name):
    fig.text(.5, .015, "Desarrollo | Analisis descriptivo | Reserva final sin evaluar",
             ha="center", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0, .09, 1, .93))
    fig.savefig(ROOT / "results/figures" / name, dpi=150, facecolor="white")
    plt.close(fig)


def run():
    verify()
    folder = ROOT / "results/metrics"
    report = json.loads((folder / "optimization_results.json").read_text())
    base = json.loads((folder / "baseline_results.json").read_text())
    summaries = {**base["summary"], **report["summary"]}
    names = ["LR_base", "LR_quadratic", "RF_base", "RF_regularized"]
    titles = ["LR base", "LR cuadratica", "RF base", "RF regularizado"]
    fig, axes = plt.subplots(1, 2, figsize=(12, 5.5))
    for ax, metric, label in zip(axes, ["f1_macro", "recall20"], ["F1 macro", "Cobertura top 20%"]):
        values = [summaries[n][f"val_{metric}"] for n in names]
        errors = [summaries[n][f"val_{metric}_sd"] for n in names]
        bars = ax.bar(titles, values, color=["#a8ceca", "#23877c", "#d99b9f", "#bc414a"],
                      yerr=errors, capsize=3)
        ax.bar_label(bars, fmt="%.3f", padding=8)
        ax.set_ylim(0, .7)
        ax.set_ylabel(label)
        ax.tick_params(axis="x", labelrotation=15)
    axes[0].axhline(.6, linestyle="--", color="#333333", label="Meta 0,60")
    axes[0].legend()
    fig.suptitle("Validacion externa: media y SD de cinco folds (no intervalos de confianza)")
    save(fig, FIGURES[0])

    trials = pd.DataFrame([
        {**t["parameters"], "outer_fold": t["outer_fold"], "inner_f1": t["inner_f1"]}
        for t in report["trials"] if t["strategy"] == "RF_regularized"
    ])
    surface = trials.groupby(PARAMS, as_index=False).inner_f1.mean()
    # This surrogate explains a finite search surface, not student outcomes.
    surrogate = RandomForestRegressor(n_estimators=300, random_state=42, n_jobs=1)
    surrogate.fit(surface[PARAMS], surface.inner_f1)
    fidelity = float(surrogate.score(surface[PARAMS], surface.inner_f1))
    fig, axes = plt.subplots(1, 3, figsize=(13, 5))
    PartialDependenceDisplay.from_estimator(
        surrogate, surface[PARAMS], features=PARAMS, ax=axes,
        grid_resolution=20, percentiles=(0, 1),
    )
    fig.suptitle("PDP del modelo auxiliar: respuesta de F1 interno a hiperparametros")
    save(fig, FIGURES[1])
    importances = dict(zip(PARAMS, surrogate.feature_importances_.tolist()))
    ordered = pd.Series(importances).sort_values()
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(ordered.index, ordered.values, color="#516d83")
    ax.bar_label(bars, fmt="%.3f", padding=5)
    ax.set_xlim(0, 1.05)
    ax.set_xlabel("Importancia por reduccion de impureza del modelo auxiliar")
    fig.suptitle("Sensibilidad descriptiva; no importancia de variables del estudiante")
    save(fig, FIGURES[2])

    interaction = surface.groupby(["max_depth", "min_samples_leaf"]).inner_f1.mean().unstack()
    fig, ax = plt.subplots(figsize=(7, 5.5))
    image = ax.imshow(interaction, cmap="YlGnBu")
    for i in range(len(interaction)):
        for j in range(len(interaction.columns)):
            ax.text(j, i, f"{interaction.iloc[i,j]:.4f}", ha="center", va="center",
                    color="white" if interaction.iloc[i,j] > interaction.to_numpy().mean() else "black")
    ax.set_xticks(range(len(interaction.columns)), interaction.columns)
    ax.set_yticks(range(len(interaction)), interaction.index)
    ax.set_xlabel("Hoja minima")
    ax.set_ylabel("Profundidad maxima")
    fig.colorbar(image, ax=ax, label="F1 interno medio")
    fig.suptitle("Profundidad x hoja: media sobre folds y numero de arboles")
    save(fig, FIGURES[3])

    fig, ax = plt.subplots(figsize=(9, 5))
    for fold in range(1, 6):
        options = sorted([t for t in report["trials"]
                          if t["strategy"] == "LR_quadratic" and t["outer_fold"] == fold],
                         key=lambda t: t["parameters"]["C"])
        ax.plot([t["parameters"]["C"] for t in options], [t["inner_f1"] for t in options],
                marker="o", label=f"Fold externo {fold}")
    ax.set_xscale("log")
    ax.set_xlabel("C (menor valor = mayor regularizacion)")
    ax.set_ylabel("F1 interno medio")
    ax.legend()
    fig.suptitle("Sensibilidad de la regresion cuadratica a C")
    save(fig, FIGURES[4])

    comparisons = {}
    for strategy, baseline in [("LR_quadratic", "LR_base"), ("RF_regularized", "RF_base")]:
        before, after = summaries[baseline], summaries[strategy]
        differences = []
        for fold in range(1, 6):
            a = next(r for r in report["folds"] if r["model"] == strategy and r["fold"] == fold)
            b = next(r for r in base["folds"] if r["model"] == baseline and r["fold"] == fold)
            differences.append({
                "fold": fold,
                "delta_f1": a["val"]["f1_macro"] - b["val"]["f1_macro"],
                "delta_recall20": a["val"]["recall20"] - b["val"]["recall20"],
            })
        comparisons[strategy] = {
            "baseline": baseline,
            "delta_f1": after["val_f1_macro"] - before["val_f1_macro"],
            "delta_coverage": after["val_recall20"] - before["val_recall20"],
            "gap_before": before["gap_f1"], "gap_after": after["gap_f1"],
            "fold_differences": differences,
        }
    evidence = {
        "surface": surface.to_dict(orient="records"),
        "surrogate": {"type": "RandomForestRegressor", "trees": 300, "seed": 42,
                      "training_r2": fidelity, "importance_mdi": importances},
        "comparisons": comparisons,
        "limitations": "Surrogate fitted to 18 aggregated search points; in-sample R2 is fidelity, not generalization. MDI and PDP depend on tested ranges. Correlated folds do not provide independent replicates.",
    }
    (folder / "optimization_sensitivity.json").write_text(
        json.dumps(evidence, indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )
    rows = "\n".join(
        f"| {name} | {summaries[name]['train_f1_macro']:.5f} | "
        f"{summaries[name]['val_f1_macro']:.5f} | {summaries[name]['val_f1_macro_sd']:.5f} | "
        f"{summaries[name]['gap_f1']:.5f} | {100*summaries[name]['val_recall20']:.2f}% |"
        for name in names
    )
    choice_rows = "\n".join(
        f"| {r['fold']} | {r['model']} | {json.dumps(r['parameters'], sort_keys=True)} |"
        for r in report["folds"]
    )
    change_rows = "\n".join(
        f"| {name} | {item['delta_f1']:+.5f} | {100*item['delta_coverage']:+.2f} pp | "
        f"{sum(d['delta_f1']>0 for d in item['fold_differences'])}/5 |"
        for name, item in comparisons.items()
    )
    images = "\n\n".join(f"![Analisis {i}](../results/figures/{f})" for i, f in enumerate(FIGURES, 1))
    top_param = max(importances, key=importances.get)
    warning_count = sum(len(t["warnings"]) for t in report["trials"]) + sum(len(r["warnings"]) for r in report["folds"])
    lr, rf = comparisons["LR_quadratic"], comparisons["RF_regularized"]
    addition = f"""
## Resultados ejecutados

Se completaron 105 evaluaciones de configuraciones (21 por fold externo),
315 ajustes internos y 10 reajustes externos. Se verificaron 7.078 predicciones
OOF, seleccion interna y pertenencia a particiones. Advertencias registradas:
{warning_count}. [Resultados y registros](../results/metrics/optimization_results.json).

| Modelo/estrategia | F1 entrenamiento | F1 validacion | SD validacion | Brecha | Cobertura 20% |
|---|---:|---:|---:|---:|---:|
{rows}

Cada estrategia puede elegir configuraciones distintas por fold. Su promedio
evalua un procedimiento de ajuste, no un unico modelo final entrenado.

| Estrategia frente a su base | Cambio F1 | Cambio cobertura | Folds con mayor F1 |
|---|---:|---:|---:|
{change_rows}

La brecha de RF pasa de {rf['gap_before']:.5f} a {rf['gap_after']:.5f}.
La de LR pasa de {lr['gap_before']:.5f} a {lr['gap_after']:.5f}.
Reducir una brecha no basta para afirmar mejora: debe considerarse tambien el
F1 externo y la cobertura. La expansion cuadratica es una intervencion sobre
la representacion, no simplemente mas regularizacion de la regresion base.
Los cambios por fold se conservan en [la evidencia de sensibilidad](../results/metrics/optimization_sensitivity.json).

En esta ejecucion, RF reduce su sobreajuste pero su F1 externo cae ligeramente
frente a la base. La regresion cuadratica mejora apenas y no resuelve el
rendimiento limitado. Ambas aumentan la cobertura unos 0,53 puntos porcentuales,
pero ninguna alcanza la meta F1 de 0,60. No se justifica presentar estas
estrategias como una mejora concluyente ni declarar un ganador definitivo.

## Configuraciones elegidas por validacion interna

| Fold externo | Estrategia | Parametros elegidos |
|---|---|---|
{choice_rows}

Si un ganador esta en un extremo del rango explorado, no se afirma que sea un
optimo global. No se ampliaron los rangos despues de observar la validacion
externa. Aun falta fijar una familia y ajustar su configuracion de produccion
sobre desarrollo con un protocolo documentado; no hay modelo final guardado.

## Sensibilidad y dependencia parcial

Para RF se promedian los F1 internos de cada configuracion sobre los cinco
entrenamientos externos. Un RandomForestRegressor auxiliar de 300 arboles,
semilla 42, aproxima esa superficie de 18 puntos. Su R2 sobre esos mismos
puntos es {fidelity:.4f}: mide fidelidad de ajuste, no generalizacion ni rendimiento
del clasificador.

Los PDP promedian la respuesta predicha al variar un hiperparametro y mantener
la distribucion de los otros. La importancia por reduccion de impureza del
auxiliar situa el mayor peso en **{top_param}** ({importances[top_param]:.3f}).
Este ranking es descriptivo, depende del rango y del modelo auxiliar y no tiene
intervalos de confianza. No corresponde a importancia de variables del alumnado.

El mapa profundidad-hoja usa directamente F1 internos observados y promedia
sobre numero de arboles y folds. Permite examinar combinaciones; no es una prueba
formal de interaccion. Las curvas de LR muestran la respuesta interna a C con
la representacion cuadratica fijada.

{images}

## Limites y siguientes comprobaciones

El mayor F1 externo observado entre estas dos estrategias es
{max(summaries[s]['val_f1_macro'] for s in STRATEGIES):.5f}.
La meta sigue siendo 0,60 y solo se declarara alcanzada si la evidencia lo
respalda. No se interpreta una diferencia pequena como significacion estadistica.
Los folds comparten datos de entrenamiento y la eleccion posterior de familia
usa desarrollo; la estimacion confirmatoria requerira el protocolo final.

Persisten pendientes las pruebas de estres con tolerancias previas, fairness
por subgrupos, calibracion, seleccion definitiva y evaluacion de la reserva.
No se han usado datos de prueba para elegir configuraciones.

## Reproduccion

```text
python -m src.optimize
python -c "from src.optimize import verify; print(verify())"
python -m src.optimization_report
```

El notebook 04 permite leer y verificar los resultados guardados, o repetir
la busqueda explicitamente. Este reporte se genera a partir de los JSON.
"""
    # Retain the pre-experiment protocol; replace only the generated results section.
    doc = ROOT / "docs/optimizacion.md"
    original = doc.read_text(encoding="utf-8").split("## Resultados ejecutados")[0].rstrip()
    original = original.replace(
        "Estado inicial del protocolo: resultados pendientes.",
        "El protocolo se registro antes de ejecutar; los resultados se presentan a continuacion."
    )
    doc.write_text(original + "\n\n" + addition.lstrip(), encoding="utf-8")
    return evidence


if __name__ == "__main__":
    run()
