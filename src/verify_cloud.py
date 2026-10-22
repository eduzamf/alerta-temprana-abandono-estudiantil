"""Verify a hosted demo with public development inputs and no credentials."""
import argparse
import json
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import numpy as np

from .data_processing import ROOT
from .inference import analyze, demo


def run(base_url):
    """Check the public API and compare inference to the unchanged local model."""
    base = base_url.rstrip("/")
    parsed = urlsplit(base)
    if parsed.scheme != "https" or parsed.username or parsed.query or parsed.path:
        raise ValueError("Supply an HTTPS origin without credentials, path or query")

    def get(path):
        with urlopen(base + path, timeout=120) as response:
            return response.read()

    def post(raw, origin=base):
        boundary = "AcademicDemoVerificationBoundary"
        prefix = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
            "filename=\"public_sample.csv\"\r\nContent-Type: text/csv\r\n\r\n"
        ).encode()
        body = prefix + raw + f"\r\n--{boundary}--\r\n".encode()
        request = Request(
            base + "/api/analyze", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                     "X-Requested-With": "local-demo", "Origin": origin},
        )
        try:
            with urlopen(request, timeout=120) as response:
                return response.status, json.load(response)
        except HTTPError as error:
            return error.code, json.load(error)

    health = json.loads(get("/health"))
    remote = json.loads(get("/api/demo"))
    local = analyze(demo(), "verification")
    if health.get("status") != "ok" or remote["model_sha256"] != local["model_sha256"]:
        raise AssertionError("Health or artifact fingerprint mismatch")
    if (remote["count"], remote["selected"]) != (40, 8):
        raise AssertionError("Unexpected sample size or capacity")
    for actual, expected in zip(remote["rows"], local["rows"]):
        for key in ["id", "source_row", "rank", "selected", "predicted"]:
            if actual[key] != expected[key]:
                raise AssertionError(f"Remote prediction mismatch: {key}")
        np.testing.assert_allclose(actual["score"], expected["score"], rtol=1e-10, atol=1e-12)
    status, uploaded = post(get("/api/sample"))
    if status != 200 or uploaded["rows"] != remote["rows"]:
        raise AssertionError("Uploaded sample differs from remote sample")
    status_missing, missing = post(get("/api/sample/missing"))
    if status_missing != 200 or missing["missing_cells"] != 1 or not missing["warnings"]:
        raise AssertionError("Missing-value case failed")
    status_invalid, _ = post(get("/api/sample/invalid"))
    status_origin, _ = post(get("/api/sample"), origin="https://other.example")
    if status_invalid != 400 or status_origin != 403:
        raise AssertionError("Invalid input or origin was not rejected")
    evidence = json.loads(get("/api/evidence"))
    final = json.loads((ROOT / "results/metrics/final_test_results.json").read_text())
    if evidence["metrics"] != final["metrics"]:
        raise AssertionError("Published metrics differ from frozen final evaluation")
    report = {
        "verified_at_utc": datetime.now(timezone.utc).isoformat(),
        "url": base, "authenticated": False,
        "health": health["status"], "model_sha256": remote["model_sha256"],
        "sample_rows": 40, "prioritized": 8, "local_predictions_match": True,
        "valid_upload_status": status, "missing_upload_status": status_missing,
        "invalid_upload_status": status_invalid, "foreign_origin_status": status_origin,
        "published_metrics_match": True,
        "scope": "Public API with development examples; not new performance evaluation",
    }
    (ROOT / "results/metrics/cloud_verification.json").write_text(
        json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    print(json.dumps(run(parser.parse_args().url), indent=2))
