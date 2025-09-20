from flask import Flask

def create_app():
    """
    Application factory function that creates and configures the Flask app.
    """
    app = Flask(__name__, static_folder='static')
    
    # Import and register blueprints
    from app.routes.webhook import webhook_bp
    app.register_blueprint(webhook_bp)
    
    # Start background tasks
    from app.services.tradovate_service import start_background_tasks
    start_background_tasks()
    
    return app
