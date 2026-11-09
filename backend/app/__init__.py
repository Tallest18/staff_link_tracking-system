from flask import Flask

from .db import connect_firestore
from .errors import register_error_handlers
from .health import health_bp
from .links import links_bp
from .staff import staff_bp


def create_app(db=None):
    """Build the Flask application and attach all of its routes.

    Tests pass in a stand-in for `db`. Normally we connect to real Firestore.
    """
    app = Flask(__name__)
    app.config["DB"] = db if db is not None else connect_firestore()
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(staff_bp, url_prefix="/api")
    app.register_blueprint(links_bp, url_prefix="/api")
    register_error_handlers(app)
    return app
