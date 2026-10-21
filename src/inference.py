"""Validation and batch inference for the local demonstration."""
import csv
import io
from functools import lru_cache

import numpy as np
import pandas as pd

from .data_processing import FEATURES, CATEGORICAL, NUMERIC, LABELS, load_development, select_predictors
from .evaluate import priority_mask
from .finalize import MODEL, digest, load_frozen

MAX_ROWS = 1000
MAX_BYTES = 200000


class InputError(ValueError):
    pass


@lru_cache(maxsize=1)
def context():
    model, metadata = load_frozen()
    development, _ = load_development()
    return model, metadata, select_predictors(development)


def parse_csv(raw):
    if not raw or len(raw) > MAX_BYTES:
        raise InputError("El CSV debe contener datos y no superar 200 KB.")
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise InputError("El archivo debe estar codificado en UTF-8.") from exc
    try:
        first = text.splitlines()[0]
        delimiter = ";" if first.count(";") > first.count(",") else ","
        rows = list(csv.reader(io.StringIO(text), delimiter=delimiter, strict=True))
    except (csv.Error, IndexError) as exc:
        raise InputError("No se pudo leer el CSV.") from exc
    headers = [v.strip() for v in rows[0]]
    if len(set(headers)) != len(headers):
        raise InputError("Hay nombres de columnas duplicados.")
    if set(headers) != set(FEATURES):
        raise InputError("Se requieren exactamente las 18 columnas de la plantilla, sin nombres, identificadores ni Target.")
    values = rows[1:]
    if any(not row for row in values):
        raise InputError("Elimine las filas vacias del CSV antes de cargarlo.")
    if not 5 <= len(values) <= MAX_ROWS:
        raise InputError("El lote debe contener entre 5 y 1.000 filas.")
    if any(len(row) != len(headers) for row in values):
        raise InputError("Hay filas con un numero de campos incorrecto.")
    frame = pd.DataFrame(values, columns=headers).replace(r"^\s*$", np.nan, regex=True)
    try:
        frame = frame.apply(pd.to_numeric, errors="raise").astype(float)
    except (ValueError, TypeError) as exc:
        raise InputError("Solo se admiten numeros, codigos numericos y celdas vacias.") from exc
    return frame.loc[:, FEATURES]


def validate(frame):
    _, _, reference = context()
    if not 5 <= len(frame) <= MAX_ROWS:
        raise InputError("El lote debe contener entre 5 y 1.000 filas.")
    try:
        X = select_predictors(frame)
    except (ValueError, TypeError) as exc:
        raise InputError("Esquema numerico invalido: use la plantilla de 18 columnas.") from exc
    if (X.isna().mean(axis=1) > .2).any() or X.isna().to_numpy().mean() > .2:
        raise InputError("Hay filas con mas del 20% de datos faltantes. Complete los datos antes de continuar.")
    for column in CATEGORICAL:
        values = X[column].dropna()
        if not values.isin(reference[column].unique()).all():
            raise InputError(f"Codigo no observado en desarrollo: {column}. No se genera una priorizacion.")
    for column in ["Previous qualification (grade)", "Admission grade"]:
        if not X[column].dropna().between(0, 200).all():
            raise InputError(f"{column}: la escala admitida es de 0 a 200.")
    for column, lower, upper in [("Age at enrollment", 1, 100), ("Application order", 0, 9)]:
        values = X[column].dropna()
        if not values.between(lower, upper).all() or not values.eq(np.floor(values)).all():
            raise InputError(f"{column}: se requieren enteros entre {lower} y {upper}.")
    warnings = []
    missing = int(X.isna().sum().sum())
    if missing:
        warnings.append(f"{missing} celdas vacias: se imputan con estadisticas del entrenamiento. El resultado requiere cautela.")
    for column in NUMERIC:
        outside = X[column].notna() & ~X[column].between(reference[column].min(), reference[column].max())
        if outside.any():
            warnings.append(f"{column}: {int(outside.sum())} valores fuera del rango observado en desarrollo.")
    return X, warnings


def analyze(frame, source):
    model, metadata, _ = context()
    if digest(MODEL) != metadata["model_sha256"]:
        raise RuntimeError("El artefacto cambio durante la sesion.")
    X, warnings = validate(frame)
    raw = model.predict_proba(X)
    probabilities = raw[:, [list(model.classes_).index(label) for label in LABELS]]
    predicted = model.predict(X)
    selected = priority_mask(probabilities[:, 0])
    order = np.argsort(-probabilities[:, 0], kind="stable")
    rows = []
    for rank, index in enumerate(order, 1):
        row = X.iloc[index]
        rows.append({
            "rank": rank, "id": f"CASO-{index+1:04d}", "source_row": int(index+2),
            "score": float(probabilities[index, 0]), "selected": bool(selected[index]),
            "predicted": str(predicted[index]), "missing": int(row.isna().sum()),
            "scores": dict(zip(LABELS, probabilities[index].tolist())),
            "features": {name: None if pd.isna(value) else float(value) for name, value in row.items()},
        })
    return {"source": source, "count": len(X), "selected": int(selected.sum()),
            "missing_cells": int(X.isna().sum().sum()), "warnings": warnings,
            "rows": rows, "model": "LR_base v1", "model_sha256": metadata["model_sha256"]}


def demo():
    # Fixed public development sample, without labels or personal identifiers.
    return context()[2].iloc[:40].copy()


def template_csv():
    return ",".join(FEATURES) + "\n"
