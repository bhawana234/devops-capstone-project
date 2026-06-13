"""
Package: service
Creates and configures the Flask app, logging, and database
"""
import sys
from flask import Flask
from flask_talisman import Talisman
from flask_cors import CORS

from service import config
from service.common import log_handlers

# Create Flask application
app = Flask(__name__)
app.config.from_object(config)

# Security and CORS
talisman = Talisman(app, content_security_policy="default-src 'self'; object-src 'none'")
CORS(app)

# Import routes AFTER app is created
from service import routes, models  # noqa: F401 E402
from service.common import error_handlers, cli_commands  # noqa: F401 E402

# Logging
log_handlers.init_logging(app, "gunicorn.error")

app.logger.info(70 * "*")
app.logger.info("ACCOUNT SERVICE RUNNING".center(70, "*"))
app.logger.info(70 * "*")

try:
    models.init_db(app)
except Exception as error:  # pylint: disable=broad-except
    app.logger.critical("%s: Cannot continue", error)
    sys.exit(4)

app.logger.info("Service initialized!")

__all__ = ["app", "talisman"]