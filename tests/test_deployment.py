"""Cloud-domain controls tested without contacting or trusting a real proxy."""
import io
import unittest
from unittest.mock import patch

from app.app import app
from app.deployment import deployment_config
from src.inference import demo


class DeploymentTests(unittest.TestCase):
    def test_local_defaults(self):
        config = deployment_config({})
        self.assertEqual(config["TRUSTED_HOSTS"], ["127.0.0.1", "localhost"])
        self.assertIsNone(config["PUBLIC_ORIGIN"])

    def test_only_exact_render_domain(self):
        for hostname in ["*", ".onrender.com", "https://demo.onrender.com",
                         "demo.onrender.com.evil.example", "demo.onrender.com/path"]:
            with self.assertRaises(ValueError):
                deployment_config({"RENDER_EXTERNAL_HOSTNAME": hostname})

    def test_cloud_origin_works_behind_http_proxy(self):
        config = deployment_config({"RENDER_EXTERNAL_HOSTNAME": "test-demo.onrender.com"})
        with patch.dict(app.config, config):
            response = app.test_client().post(
                "/api/analyze", base_url="http://test-demo.onrender.com",
                data={"file": (io.BytesIO(demo().to_csv(index=False).encode()), "sample.csv")},
                headers={"X-Requested-With": "local-demo",
                         "Origin": "https://test-demo.onrender.com"},
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json["selected"], 8)
            self.assertIn("Strict-Transport-Security", response.headers)

    def test_foreign_origin_and_host_rejected(self):
        config = deployment_config({"RENDER_EXTERNAL_HOSTNAME": "test-demo.onrender.com"})
        with patch.dict(app.config, config):
            client = app.test_client()
            for origin in ["https://evil.example", "null", "http://test-demo.onrender.com"]:
                response = client.post(
                    "/api/analyze", base_url="http://test-demo.onrender.com",
                    headers={"X-Requested-With": "local-demo", "Origin": origin},
                )
                self.assertEqual(response.status_code, 403)
            self.assertEqual(client.get("/", base_url="https://other.onrender.com").status_code, 400)

    def test_proxy_headers_cannot_expand_hosts(self):
        response = app.test_client().get(
            "/", base_url="http://evil.example",
            headers={"X-Forwarded-Host": "localhost", "X-Forwarded-Proto": "https"},
        )
        self.assertEqual(response.status_code, 400)

    def test_health_requires_model_integrity(self):
        self.assertEqual(app.test_client().get("/health").json["status"], "ok")
        with patch("app.app.digest", return_value="changed"):
            self.assertEqual(app.test_client().get("/health").status_code, 503)


if __name__ == "__main__":
    unittest.main()
