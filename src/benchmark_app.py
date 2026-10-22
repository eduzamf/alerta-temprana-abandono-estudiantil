"""Measure warm CSV requests using development records, never final-test rows."""
import io
import json
import platform
from statistics import median
from time import perf_counter

from app.app import app
from .data_processing import ROOT
from .inference import context


def run():
    """Save ten local request timings, excluding initialization and network."""
    model, metadata, reference = context()
    payload = reference.iloc[:1000].to_csv(index=False).encode("utf-8")
    durations = []
    with app.test_client() as client:
        for repetition in range(11):
            start = perf_counter()
            response = client.post(
                "/api/analyze",
                data={"file": (io.BytesIO(payload), "development_1000.csv")},
                headers={"X-Requested-With": "local-demo"},
            )
            elapsed = perf_counter() - start
            if response.status_code != 200:
                raise RuntimeError(response.get_data(as_text=True))
            result = response.get_json()
            if result["count"] != 1000 or result["selected"] != 200:
                raise AssertionError("Unexpected batch count or ranking capacity")
            if repetition:
                durations.append(elapsed)
    seconds = median(durations)
    report = {
        "scope": "Flask test client: parsing, validation, inference and JSON; no network or browser",
        "input": "first 1000 development rows; not independent evaluation",
        "rows": 1000, "repetitions": 10, "warmups": 1,
        "python": platform.python_version(), "platform": platform.platform(),
        "processor": platform.processor(), "model_sha256": metadata["model_sha256"],
        "seconds": durations, "median_seconds": seconds,
        "records_per_second": 1000 / seconds,
        "target_seconds": 5, "target_met": seconds <= 5,
    }
    target = ROOT / "results/metrics/app_benchmark.json"
    target.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
