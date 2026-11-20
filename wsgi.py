"""Production WSGI entrypoint for Gunicorn, Render, PythonAnywhere, and Docker."""
from campaign_engine.webapp import create_app

app = create_app()
application = app  # compatibility alias for PythonAnywhere WSGI
