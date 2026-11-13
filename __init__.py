
from backend.api.chat import chat_bp


def register_api(app):
    app.register_blueprint(
        chat_bp,
        url_prefix="/api"
    )
