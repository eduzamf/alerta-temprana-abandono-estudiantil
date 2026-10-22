"""Gunicorn entry point: warm the existing model without training."""
from app.app import app
from src.inference import context

context()
