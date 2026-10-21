"""Reproducible demonstration inputs derived only from public development rows."""
import numpy as np

from .data_processing import ROOT
from .inference import demo

FILES = {"valid": "01_lote_valido.csv", "missing": "02_nota_vacia.csv",
         "invalid": "03_carrera_invalida.csv"}


def case_frame(kind):
    if kind not in FILES:
        raise ValueError("Unknown demonstration case")
    frame = demo().copy()
    if kind == "missing":
        frame.loc[frame.index[0], "Admission grade"] = np.nan
    elif kind == "invalid":
        frame.loc[frame.index[0], "Course"] = 999999
    return frame


def run():
    folder = ROOT / "data/examples"
    folder.mkdir(exist_ok=True)
    for kind, filename in FILES.items():
        case_frame(kind).to_csv(folder / filename, index=False)


if __name__ == "__main__":
    run()
