from flask import Flask


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")

    with app.app_context():
        from . import main

        app.register_blueprint(main.bp)

    return app
