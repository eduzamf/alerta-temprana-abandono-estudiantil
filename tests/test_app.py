import io
import json
import unittest

import numpy as np
import pandas as pd

from app.app import app
from src.data_processing import ROOT
from src.finalize import MODEL, digest
from src.inference import InputError, analyze, context, demo, parse_csv, validate


class AppTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = app.test_client()
        cls.raw = demo().to_csv(index=False).encode()

    def post(self, raw=None, **kwargs):
        return self.client.post("/api/analyze",
            data={"file": (io.BytesIO(self.raw if raw is None else raw), "sample.csv")},
            headers=kwargs.get("headers", {"X-Requested-With": "local-demo"}))

    def test_demo_and_model_match(self):
        result = self.client.get("/api/demo").json
        self.assertEqual(result["count"], 40)
        self.assertEqual(result["selected"], 8)
        model = context()[0]
        scores = model.predict_proba(demo())[:, list(model.classes_).index("Dropout")]
        for row in result["rows"]:
            self.assertAlmostEqual(row["score"], scores[row["source_row"]-2])
        self.assertEqual(digest(MODEL), result["model_sha256"])

    def test_upload_matches_demo(self):
        response = self.post()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["rows"], self.client.get("/api/demo").json["rows"])

    def test_utf8_semicolon(self):
        raw = b"\xef\xbb\xbf" + demo().to_csv(index=False, sep=";").encode()
        np.testing.assert_allclose(parse_csv(raw), demo())

    def test_target_and_personal_columns_rejected(self):
        for column in ["Target", "name", "email"]:
            raw = demo().assign(**{column: "private"}).to_csv(index=False).encode()
            self.assertEqual(self.post(raw).status_code, 400)

    def test_unknown_course_rejected(self):
        frame = demo()
        frame.loc[frame.index[0], "Course"] = 999999
        response = self.post(frame.to_csv(index=False).encode())
        self.assertEqual(response.status_code, 400)
        self.assertIn("Course", response.json["error"])

    def test_excess_missing_rejected(self):
        frame = demo().astype(float)
        frame.iloc[0, :4] = np.nan
        with self.assertRaises(InputError):
            validate(frame)

    def test_small_missing_warning(self):
        frame = demo().astype(float)
        frame.iloc[0, 0] = np.nan
        result = analyze(frame, "test")
        self.assertEqual(result["missing_cells"], 1)
        self.assertTrue(result["warnings"])
        self.assertEqual(sum(r["selected"] for r in result["rows"]), 8)

    def test_infinite_and_grades_rejected(self):
        for value in [np.inf, 201, -1]:
            frame = demo().astype(float)
            frame.loc[frame.index[0], "Admission grade"] = value
            with self.assertRaises(InputError):
                validate(frame)

    def test_small_batch_rejected(self):
        self.assertEqual(self.post(demo().iloc[:4].to_csv(index=False).encode()).status_code, 400)

    def test_duplicate_headers_rejected(self):
        text = self.raw.decode()
        text = text.replace("Marital status", "Course", 1)
        self.assertEqual(self.post(text.encode()).status_code, 400)

    def test_request_origin_guard(self):
        self.assertEqual(self.post(headers={}).status_code, 403)
        self.assertEqual(self.post(headers={"X-Requested-With": "local-demo", "Origin": "https://evil.example"}).status_code, 403)

    def test_size_and_filename_limits(self):
        self.assertEqual(self.post(b"x"*300000).status_code, 413)
        response = self.client.post("/api/analyze", data={"file": (io.BytesIO(self.raw), "file.exe")},
                                    headers={"X-Requested-With": "local-demo"})
        self.assertEqual(response.status_code, 400)

    def test_evidence_matches_final_test(self):
        final = json.loads((ROOT/"results/metrics/final_test_results.json").read_text())
        self.assertEqual(self.client.get("/api/evidence").json["metrics"], final["metrics"])

    def test_resources_and_headers(self):
        for path in ["/", "/assets/app.js", "/assets/app.css", "/api/template", "/api/sample",
                     "/api/schema", "/evidence/confusion.png"]:
            response = self.client.get(path)
            self.assertEqual(response.status_code, 200, path)
            self.assertEqual(response.headers["Cache-Control"], "no-store")
            response.close()
        self.assertEqual(self.client.get("/").headers["X-Frame-Options"], "DENY")
        self.assertEqual(self.client.get("/", base_url="http://evil.example").status_code, 400)


if __name__ == "__main__":
    unittest.main()
