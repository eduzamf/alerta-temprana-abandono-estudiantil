"""Development-only EDA with shared evidence for figures and documentation."""
import json

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from .data_processing import (
    CATEGORICAL, DATA_SHA256, FEATURES, LABELS, NUMERIC, ROOT,
    SPLIT_SHA256, load_development,
)

COLORS = ["#bc414a", "#bd851f", "#23877c"]
SHORT = {
    "Application order": "Orden de solicitud",
    "Previous qualification (grade)": "Nota previa",
    "Admission grade": "Nota de admision",
    "Age at enrollment": "Edad al matricularse",
}
FIGURES = [
    ("eda_01_clases.png", "Distribucion de las clases"),
    ("eda_02_numericas.png", "Distribuciones de las variables numericas"),
    ("eda_03_notas_clase.png", "Notas y edad por resultado"),
    ("eda_04_edad_resultado.png", "Composicion de resultados por edad"),
    ("eda_05_correlaciones.png", "Correlaciones entre variables numericas"),
    ("eda_06_categorias.png", "Cardinalidad de predictores categoricos"),
    ("eda_07_subgrupos.png", "Representacion de subgrupos"),
]
AGE_LABELS = ["Menos de 20", "20-24", "25-34", "35 o mas"]


def age_groups(values):
    """Fixed descriptive intervals; not chosen using outcome differences."""
    return pd.cut(values, [-np.inf, 20, 25, 35, np.inf],
                  labels=AGE_LABELS, right=False)


def subgroup_series(frame):
    """Audit-only fields do not change the predictive feature contract."""
    return {
        "Genero (codigo)": frame["Gender"].astype(str),
        "Edad": age_groups(frame["Age at enrollment"]),
        "Nacionalidad (codigo)": frame["Nacionality"].astype(str),
        "Necesidades especiales (codigo)": frame["Educational special needs"].astype(str),
        "Beca (codigo; solo auditoria)": frame["Scholarship holder"].astype(str),
        "Deuda (codigo; solo auditoria)": frame["Debtor"].astype(str),
    }


def summarize(frame):
    """Compute descriptive evidence only, never fit or score a predictor."""
    numeric = {}
    for column in NUMERIC:
        values = frame[column]
        q1, q3 = values.quantile([0.25, 0.75])
        low, high = float(q1 - 1.5 * (q3 - q1)), float(q3 + 1.5 * (q3 - q1))
        numeric[column] = {
            **{k: float(v) for k, v in values.describe().items()},
            "iqr_lower": low, "iqr_upper": high,
            "iqr_flags": int(((values < low) | (values > high)).sum()),
        }
    categorical = {}
    for column in CATEGORICAL:
        counts = frame[column].value_counts().sort_index()
        categorical[column] = {
            "levels": len(counts),
            "counts": {str(k): int(v) for k, v in counts.items()},
            "levels_under_10": int((counts < 10).sum()),
            "rows_in_levels_under_10": int(counts[counts < 10].sum()),
        }
    subgroups = {}
    for column, values in subgroup_series(frame).items():
        subgroups[column] = {
            str(k): int(v) for k, v in values.value_counts(sort=False).items()
        }
    age_outcomes = pd.crosstab(
        age_groups(frame["Age at enrollment"]), frame.Target, dropna=False
    ).reindex(index=AGE_LABELS, columns=LABELS, fill_value=0)
    invalid = {}
    for column in ["Previous qualification (grade)", "Admission grade"]:
        invalid[column] = int((~frame[column].between(0, 200)).sum())
    invalid["Application order"] = int((~frame["Application order"].between(0, 9)).sum())
    invalid["Age at enrollment"] = int((frame["Age at enrollment"] <= 0).sum())
    for column in ["Gender", "Displaced", "Educational special needs",
                   "International", "Daytime/evening attendance",
                   "Scholarship holder", "Debtor"]:
        invalid[column] = int((~frame[column].isin([0, 1])).sum())
    return {
        "scope": "development only; no final-test evaluation",
        "dataset_sha256": DATA_SHA256, "partitions_sha256": SPLIT_SHA256,
        "rows": len(frame), "predictor_count": len(FEATURES),
        "class_counts": {c: int(frame.Target.eq(c).sum()) for c in LABELS},
        "missing_cells": int(frame.isna().sum().sum()),
        "exact_duplicates": int(frame.duplicated().sum()),
        "duplicate_feature_rows": int(frame.duplicated(subset=FEATURES).sum()),
        "numeric": numeric, "categorical": categorical,
        "subgroup_counts": subgroups,
        "age_outcomes": age_outcomes.astype(int).to_dict(orient="index"),
        "spearman_numeric": frame[NUMERIC].corr(method="spearman").to_dict(),
        "range_check_violations": invalid,
        "range_check_note": "Limited checks, not a complete validation of all category codes.",
    }


def save_figure(fig, name, output):
    """Keep provenance visible on every chart."""
    fig.text(0.5, 0.012, "UCI 697 | Solo desarrollo (n = 3539) | Sin evaluar la reserva final",
             ha="center", fontsize=9, color="#555555")
    fig.tight_layout(rect=(0, 0.04, 1, 0.95))
    fig.savefig(output / name, dpi=150, facecolor="white")
    plt.close(fig)


def draw_figures(frame, summary, output):
    output.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False})
    fig, ax = plt.subplots(figsize=(9, 5))
    counts = [summary["class_counts"][c] for c in LABELS]
    bars = ax.bar(LABELS, counts, color=COLORS)
    ax.bar_label(bars, labels=[f"{n} ({n / len(frame):.1%})" for n in counts], padding=5)
    ax.set_ylim(0, max(counts) * 1.2)
    ax.set_ylabel("Estudiantes")
    fig.suptitle("Resultados observados en desarrollo")
    save_figure(fig, FIGURES[0][0], output)

    fig, axes = plt.subplots(2, 2, figsize=(11, 7))
    for ax, column in zip(axes.flat, NUMERIC):
        bins = np.arange(-0.5, 10.5) if column == "Application order" else 24
        ax.hist(frame[column], bins=bins, color="#23877c", edgecolor="white")
        ax.set_title(SHORT[column])
        ax.set_ylabel("Estudiantes")
    fig.suptitle("Variables numericas disponibles al matricularse")
    save_figure(fig, FIGURES[1][0], output)

    fig, axes = plt.subplots(1, 3, figsize=(12, 5))
    for ax, column in zip(axes, NUMERIC[1:]):
        plot = ax.boxplot([frame.loc[frame.Target.eq(c), column] for c in LABELS],
                          tick_labels=LABELS, patch_artist=True,
                          flierprops={"markersize": 2, "alpha": 0.3})
        for box, color in zip(plot["boxes"], COLORS):
            box.set_facecolor(color)
        ax.set_title(SHORT[column])
    fig.suptitle("Distribuciones por clase: asociaciones, no efectos causales")
    save_figure(fig, FIGURES[2][0], output)

    table = pd.DataFrame.from_dict(summary["age_outcomes"], orient="index")[LABELS]
    proportions = table.div(table.sum(axis=1), axis=0) * 100
    fig, ax = plt.subplots(figsize=(10, 5))
    bottom = np.zeros(len(table))
    for color, label in zip(COLORS, LABELS):
        ax.bar(table.index, proportions[label], bottom=bottom, label=label, color=color)
        bottom += proportions[label].to_numpy()
    ax.set_xticks(range(len(table)), [f"{g}\nn={table.loc[g].sum()}" for g in table.index])
    ax.set_ylabel("Porcentaje dentro de cada grupo")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, 1.16), ncol=3, frameon=False)
    fig.suptitle("Composicion de resultados por edad")
    save_figure(fig, FIGURES[3][0], output)

    corr = pd.DataFrame(summary["spearman_numeric"]).loc[NUMERIC, NUMERIC]
    fig, ax = plt.subplots(figsize=(8, 6))
    plot = ax.imshow(corr, cmap="RdBu_r", vmin=-1, vmax=1)
    labels = [SHORT[c] for c in NUMERIC]
    ax.set_xticks(range(4), labels, rotation=25, ha="right")
    ax.set_yticks(range(4), labels)
    for i in range(4):
        for j in range(4):
            value = corr.iloc[i, j]
            ax.text(j, i, f"{value:.2f}", ha="center", va="center",
                    color="white" if abs(value) > 0.7 else "black")
    fig.colorbar(plot, ax=ax, label="Spearman")
    fig.suptitle("Correlaciones: solo predictores numericos")
    save_figure(fig, FIGURES[4][0], output)

    cardinalities = pd.Series({c: s["levels"] for c, s in summary["categorical"].items()})
    cardinalities = cardinalities.sort_values()
    fig, ax = plt.subplots(figsize=(11, 7))
    bars = ax.barh(cardinalities.index, cardinalities.values, color="#bd851f")
    ax.bar_label(bars, padding=4)
    ax.set_xlim(0, cardinalities.max() * 1.15)
    ax.set_xlabel("Categorias observadas")
    fig.suptitle("Codigos categoricos: no son cantidades continuas")
    save_figure(fig, FIGURES[5][0], output)

    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for ax, (name, counts) in zip(axes.flat, summary["subgroup_counts"].items()):
        series = pd.Series(counts)
        if "Nacionalidad" in name:
            # Visual grouping only; exact counts for every code remain in JSON.
            series = pd.Series({"Codigo 1": series.get("1", 0),
                                "Otros codigos": series.drop("1", errors="ignore").sum()})
        bars = ax.bar(series.index, series.values, color="#516d83")
        ax.bar_label(bars, padding=3, fontsize=9)
        ax.set_ylim(0, max(series.max() * 1.2, 1))
        ax.set_title(name, fontsize=10)
        ax.tick_params(axis="x", labelrotation=15)
        ax.set_ylabel("Estudiantes")
    fig.suptitle("Representacion: los grupos pequenos requieren cautela")
    save_figure(fig, FIGURES[6][0], output)


def write_document(summary, destination):
    """Render tables directly from the same evidence consumed by plots."""
    n = summary["rows"]
    numeric_rows = "\n".join(
        f"| {c} | {s['mean']:.2f} | {s['50%']:.2f} | {s['min']:.2f} | "
        f"{s['max']:.2f} | {s['iqr_flags']} |"
        for c, s in summary["numeric"].items()
    )
    class_rows = "\n".join(
        f"| {c} | {count} | {100 * count / n:.2f}% |"
        for c, count in summary["class_counts"].items()
    )
    category_rows = "\n".join(
        f"| {c} | {s['levels']} | {s['levels_under_10']} | "
        f"{s['rows_in_levels_under_10']} |"
        for c, s in summary["categorical"].items()
    )
    subgroup_rows = "\n".join(
        f"| {name} | {group} | {count} |"
        for name, groups in summary["subgroup_counts"].items()
        for group, count in groups.items()
    )
    image_blocks = "\n\n".join(
        f"### Figura {i}: {title}\n\n![{title}](../results/figures/{name})"
        for i, (name, title) in enumerate(FIGURES, 1)
    )
    correlation = summary["spearman_numeric"]["Admission grade"]["Previous qualification (grade)"]
    content = f"""# Analisis exploratorio de datos

## Alcance y procedencia

Este analisis utiliza exclusivamente las **{n} filas de desarrollo** del dataset
UCI 697. Las 885 filas de reserva no se utilizan para explorar variables,
seleccionar modelos ni medir su rendimiento. Se conserva el manifiesto original
y sus cinco folds de 708, 708, 708, 708 y 707 filas.

La fuente contiene 36 predictores y Target; el contrato de modelado conserva
18 variables de matricula. [Fuente, licencia CC BY 4.0 y atribucion](../data/README.md).
Las categorias y sus codigos se interpretan con el diccionario oficial, no como
escalas numericas. El indice de fila sirve para trazabilidad, nunca como predictor.

Este documento y sus graficos se generan con `python -m src.eda`.
La evidencia completa esta en [eda.json](../results/metrics/eda.json);
la integridad se comprueba mediante [data_audit.json](../results/metrics/data_audit.json).
Los valores redondeados son descriptivos, no resultados de modelos.

## Calidad y disponibilidad temporal

- Celdas nulas en desarrollo: {summary['missing_cells']}.
- Filas exactamente duplicadas: {summary['exact_duplicates']}.
- Filas repetidas en las 18 variables predictoras: {summary['duplicate_feature_rows']}.
- Incumplimientos de los controles de rango implementados: {sum(summary['range_check_violations'].values())}.

Los controles verifican notas entre 0 y 200, orden de solicitud entre 0 y 9,
edad positiva y algunos indicadores binarios. No sustituyen una validacion
completa del diccionario ni descartan errores de captura. No tener valores nulos
tampoco garantiza que todos los codigos sean informativos: existen categorias
que representan informacion desconocida.

Se excluyen los 12 indicadores de rendimiento semestral por ser posteriores al
momento de prediccion. Tambien se excluyen deuda, pagos al dia, beca y los tres
indicadores economicos por no haber confirmado su temporalidad al matricularse.
Beca y deuda se describen solo para auditoria retrospectiva, no como predictores.
Las columnas adicionales del frame no deben introducirse automaticamente al modelo.

## Clases y desbalance

| Clase | Estudiantes | Porcentaje |
|---|---:|---:|
{class_rows}

Graduate es la clase mayoritaria. Enrolled expresa permanencia al corte, no
graduacion ni abandono confirmado. La comparacion futura usara F1 macro y
metricas por clase; accuracy por si sola podria ocultar errores en las clases
menos frecuentes. La cobertura de abandono en el 20% priorizado responde a un
supuesto de capacidad de apoyo, no a una capacidad institucional ya validada.

No se aplica sobremuestreo ni balanceo al conjunto completo. Cualquier
tratamiento del desbalance se ajustara exclusivamente dentro del entrenamiento.

## Variables numericas y valores atipicos

| Variable | Media | Mediana | Minimo | Maximo | Fuera de 1,5 IQR |
|---|---:|---:|---:|---:|---:|
{numeric_rows}

La regla IQR senala observaciones para revisar; no prueba que sean errores.
No se eliminaron estudiantes de mayor edad ni se recortaron notas. El orden de
solicitud es discreto: una bandera IQR no implica una solicitud invalida.
Imputacion, escalado o limites aprendidos se ajustaran dentro de cada fold,
nunca usando toda la validacion o la reserva.

Las cajas por clase muestran solapamiento de distribuciones: diferencias entre
grupos no equivalen a separacion individual perfecta. Son asociaciones
observacionales, no evidencia de que modificar una nota o una edad cambie
causalmente el resultado.

## Correlaciones

Se calcula Spearman exclusivamente entre las cuatro variables numericas.
La correlacion entre nota previa y nota de admision es **{correlation:.3f}**.
Esta relacion no justifica por si sola eliminar una variable: su utilidad se
evaluara con validacion. No se correlacionan codigos nominales de carreras,
nacionalidades u ocupaciones como si fueran cantidades.

## Variables categoricas

| Predictor | Categorias | Categorias con menos de 10 casos | Filas en esas categorias |
|---|---:|---:|---:|
{category_rows}

El umbral de 10 se usa solo como descripcion de escasez, no como regla de
agrupacion seleccionada. Categorias poco frecuentes pueden generar estimaciones
inestables. Se mantendra codificacion nominal con manejo de categorias no vistas;
cualquier agrupacion debera evaluarse dentro de entrenamiento. El EDA no revierte
la evidencia previa de que agrupar categorias no mejoro el F1 de la regresion.

## Representacion y futura auditoria de equidad

Los intervalos de edad se fijan como menos de 20, 20-24, 25-34 y 35 o mas anos.
Son intervalos descriptivos, no umbrales de elegibilidad para recibir apoyo.

| Dimension | Grupo/codigo | Estudiantes |
|---|---|---:|
{subgroup_rows}

La figura de nacionalidad agrupa codigo 1 y otros codigos unicamente para
legibilidad; la tabla y el JSON conservan todos los grupos. Las diferencias de
tamano y la composicion por edad no son metricas de discriminacion del modelo.
Todavia faltan tasas de seleccion, cobertura y falsos positivos por subgrupo,
con conteos e intervalos de Wilson calculados sobre predicciones de validacion.
Los grupos pequenos no permiten conclusiones fuertes sobre equidad.

## Visualizaciones

{image_blocks}

## Decisiones y limitaciones

Se mantienen las particiones historicas, las 18 variables y las observaciones
sin borrados automaticos. El preprocesamiento estadistico se ajustara dentro
de cada entrenamiento. Los graficos orientan hipotesis y controles, pero no
demuestran rendimiento, equidad, causalidad ni generalizacion local.

El origen institucional portugues y las categorias administrativas limitan la
transferencia directa a Ecuador. No existe aqui validacion temporal ni externa.
La reserva sigue sin evaluacion; el analisis de errores, la auditoria del modelo,
las pruebas de estres y la evaluacion final se documentaran en fases posteriores.

## Referencia

Realinho, V., Vieira Martins, M., Machado, J., & Baptista, L. (2021).
Predict Students' Dropout and Academic Success [Dataset]. UCI Machine Learning
Repository. https://doi.org/10.24432/C5MC89
"""
    destination.write_text(content, encoding="utf-8")


def run():
    frame, _ = load_development()
    summary = summarize(frame)
    output = ROOT / "results/metrics/eda.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    draw_figures(frame, summary, ROOT / "results/figures")
    write_document(summary, ROOT / "docs/analisis_datos.md")
    return summary


if __name__ == "__main__":
    evidence = run()
    print(json.dumps({
        "rows": evidence["rows"], "class_counts": evidence["class_counts"],
        "figures": len(FIGURES), "test_evaluated": False,
    }, indent=2))
