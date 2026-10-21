"""Local-only interface for the frozen academic prototype."""
import argparse
import json
from pathlib import Path

from flask import Flask, jsonify, render_template, request, Response, send_file
from werkzeug.exceptions import HTTPException

from src.data_processing import ROOT
from src.inference import InputError, analyze, context, demo, parse_csv, template_csv
from src.data_processing import FEATURES, CATEGORICAL

app = Flask(__name__, static_folder="assets", template_folder="templates")
app.config.update(MAX_CONTENT_LENGTH=256000, MAX_FORM_MEMORY_SIZE=256000,
                  MAX_FORM_PARTS=2, TRUSTED_HOSTS=["127.0.0.1", "localhost"])


@app.before_request
def local_request():
    if request.method == "POST" and (
        request.headers.get("X-Requested-With") != "local-demo"
        or (request.headers.get("Origin") and request.headers["Origin"] != request.host_url.rstrip("/"))
    ):
        return jsonify(error="Solicitud no autorizada desde otro origen."), 403


@app.after_request
def security_headers(response):
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "no-referrer"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'"
    )
    return response


@app.get("/")
def index():
    return render_template("index.html")


@app.get("/api/evidence")
def evidence():
    final = json.loads((ROOT / "results/metrics/final_test_results.json").read_text())
    return jsonify(metrics=final["metrics"], ranking=final["ranking"], target_met=final["target_met"])


@app.get("/api/demo")
def demo_results():
    return jsonify(analyze(demo(), "Muestra UCI: 40 casos de desarrollo"))


@app.get("/api/template")
def template():
    return Response(template_csv(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=plantilla_18_variables.csv"})


@app.get("/api/schema")
def schema():
    reference = context()[2]
    return jsonify([{"column": name, "values": sorted(reference[name].unique().tolist())
                     if name in CATEGORICAL else None} for name in FEATURES])


@app.get("/api/sample")
def sample():
    return Response(demo().to_csv(index=False), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=muestra_publica_desarrollo.csv"})


@app.get("/evidence/confusion.png")
def confusion():
    return send_file(ROOT / "results/figures/final_test_confusion.png")


@app.post("/api/analyze")
def analyze_csv():
    if "file" not in request.files:
        raise InputError("Seleccione un archivo CSV.")
    upload = request.files["file"]
    if not upload.filename or Path(upload.filename).suffix.lower() != ".csv":
        raise InputError("Solo se admiten archivos .csv.")
    # Total request size is below the multipart in-memory spooling threshold.
    frame = parse_csv(upload.read())
    return jsonify(analyze(frame, "CSV cargado en esta sesion"))


@app.errorhandler(InputError)
def input_error(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(HTTPException)
def http_error(error):
    return jsonify(error="Archivo demasiado grande." if error.code == 413 else "Solicitud no valida."), error.code


@app.errorhandler(Exception)
def unexpected_error(error):
    # Do not expose uploaded content or filesystem details to the browser.
    return jsonify(error="No se pudo completar el analisis. Verifique el modelo y las dependencias."), 500


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5057)
    args = parser.parse_args()
    app.run(host="127.0.0.1", port=args.port, debug=False, threaded=False)
