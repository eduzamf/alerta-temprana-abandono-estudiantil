"""Explicit host configuration for local use or the assigned Render domain."""
import re


def deployment_config(environ):
    """Trust only the exact Render hostname, never a wildcard or proxy header."""
    hostname = environ.get("RENDER_EXTERNAL_HOSTNAME", "").strip().lower()
    if hostname and not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.onrender\.com", hostname):
        raise ValueError("RENDER_EXTERNAL_HOSTNAME must be an exact onrender.com hostname")
    return {
        "TRUSTED_HOSTS": ["127.0.0.1", "localhost"] + ([hostname] if hostname else []),
        "PUBLIC_ORIGIN": f"https://{hostname}" if hostname else None,
        "DEPLOYMENT_LABEL": "Demo pública" if hostname else "Entorno local",
    }
