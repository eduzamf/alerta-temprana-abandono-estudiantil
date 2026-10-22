"""Check local documentation links, executed notebooks and frozen evidence."""
import json
import re
from urllib.parse import unquote

from .data_processing import ROOT
from .finalize import MODEL, digest


def run():
    """Return an audit summary without training or modifying scientific results."""
    required = [
        "README.md", "LICENSE", ".gitignore", "requirements.txt",
        "docs/planificacion.md", "docs/analisis_datos.md",
        "docs/arquitectura.md", "docs/optimizacion.md",
        "docs/consideraciones_eticas.md", "docs/manual_usuario.md",
        "data/README.md", "models/README.md", "app/app.py",
    ]
    errors = [f"Missing {name}" for name in required if not (ROOT / name).is_file()]
    checked = 0
    documents = [ROOT / "README.md", *sorted((ROOT / "docs").glob("*.md")),
                 ROOT / "data/README.md", ROOT / "models/README.md"]
    for document in documents:
        text = document.read_text(encoding="utf-8")
        for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            if link.startswith(("http:", "https:", "#", "mailto:")):
                continue
            target = unquote(link.split("#")[0].strip("<>"))
            checked += 1
            if not (document.parent / target).exists():
                errors.append(f"Broken link in {document.name}: {target}")
    notebooks = sorted((ROOT / "notebooks").glob("*.ipynb"))
    if len(notebooks) != 5:
        errors.append("Expected five notebooks")
    for path in notebooks:
        notebook = json.loads(path.read_text(encoding="utf-8"))
        for index, cell in enumerate(notebook["cells"]):
            if cell["cell_type"] != "code" or not "".join(cell["source"]).strip():
                continue
            if cell.get("execution_count") is None:
                errors.append(f"Unexecuted cell: {path.name}:{index}")
            if any(out.get("output_type") == "error" for out in cell.get("outputs", [])):
                errors.append(f"Error output: {path.name}:{index}")
    results = json.loads((ROOT / "results/metrics/final_test_results.json").read_text())
    if digest(MODEL) != results["model_sha256"]:
        errors.append("Final artifact hash differs from evaluated artifact")
    if errors:
        raise AssertionError("\n".join(errors))
    return {"local_links_checked": checked, "executed_notebooks": len(notebooks),
            "model_sha256": results["model_sha256"],
            "scope": "Local files only; does not certify videos, legal compliance or public hosting"}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
