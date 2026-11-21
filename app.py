import os
from flask import Flask, jsonify, render_template
from flask_cors import CORS
from config import Config
from models import db
from routes.quiz_routes import quiz_bp
from routes.creator_routes import creator_bp
from routes.dashboard_routes import dashboard_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    CORS(app)

    # Register blueprints
    app.register_blueprint(quiz_bp)
    app.register_blueprint(creator_bp)
    app.register_blueprint(dashboard_bp)

    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        if hasattr(error, 'description') and isinstance(error.description, dict):
            return jsonify(error.description), 404
        return render_template('base.html', not_found=True), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({'error': 'Internal server error occurred.'}), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return jsonify({'error': 'Access denied / Forbidden'}), 403

    @app.errorhandler(401)
    def unauthorized_error(error):
        return jsonify({'error': 'Unauthorized. Missing valid access token.'}), 401

    # Ensure tables exist
    with app.app_context():
        db.create_all()

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    print(f"🚀 BondQuiz server launching at http://127.0.0.1:{port}")
    app.run(host='0.0.0.0', port=port, debug=debug)
