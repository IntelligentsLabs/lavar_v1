import os
import logging
from flask import Flask, request
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
#from initialize import initialize_tools_and_llms

# Load environment variables and initialize tools and LLMs
load_dotenv()
#initialize_tools_and_llms()

# Initialize Flask app
app = Flask(__name__)
app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY",
                                         "default-secret-key")

# Enable CORS and JWT authentication
CORS(app)
jwt = JWTManager(app)  # Initialize JWT with the Flask app

# Configure logging
logging.basicConfig(level=logging.INFO)

# Import and register API Blueprint
#from app.api import custom_llm
from app.api.webhook import webhook as webhook_blueprint
from app.api.custom_llm import custom_llm as custom_llm_blueprint

app.register_blueprint(webhook_blueprint, url_prefix='/api/webhook')
app.register_blueprint(custom_llm_blueprint, url_prefix='/api/custom_llm')


# ------------------------------
# Define Routes
# ------------------------------
@app.get('/')
def index():
    """Health check endpoint."""
    return {"message": "Server is running..."}


@app.get('/endpoints')
def list_endpoints():
    """Lists all registered API endpoints."""
    output = []
    for rule in app.url_map.iter_rules():
        if rule.endpoint != 'static':
            methods = ','.join(rule.methods)
            output.append({"endpoint": rule.rule, "methods": methods})
    return {"endpoints": output}


# ------------------------------
# Run the Application
# ------------------------------
def main():
    """Start the Flask server."""
    port = int(os.getenv('PORT', 5000))
    print(f"Running on port: {port}")
    app.run(port=port, debug=True)


if __name__ == '__main__':
    main()