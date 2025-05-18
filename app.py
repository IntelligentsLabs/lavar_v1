# app.py (at the project root)

import os
import logging
from logging.handlers import RotatingFileHandler # Optional: for log rotation

from flask import Flask, jsonify
from flask_caching import Cache # Import Cache
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv

# --- Load Environment Variables FIRST ---
# This ensures environment variables are available for configuration
load_dotenv()
# --- End Load Environment Variables ---

# --- Initialize Flask App ---
# Create the main Flask application instance
app = Flask(__name__)
# --- End Initialize Flask App ---

# --- Configure Logging ---
# Configure logging settings early so subsequent steps are logged
log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
log_level = getattr(logging, log_level_str, logging.INFO)
log_format = '%(asctime)s [%(levelname)s] %(name)s: %(message)s (%(pathname)s:%(lineno)d)' # Added pathname and lineno

# logging.basicConfig(level=log_level, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
# --- Ensure data directory exists ---
DATA_DIR = 'data' # Define data directory name
LOG_FILE_PATH = os.path.join(DATA_DIR, 'app.log') # Define log file path

try:
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
        print(f"Created directory: {DATA_DIR}")
except OSError as e:
    print(f"Error creating directory {DATA_DIR}: {e}")

# Decide if you want to exit or continue without file logging
# --- Configure basicConfig to use a base handler (StreamHandler by default) ---
# We will add file handler separately to the root logger.
# This setup ensures that libraries using logging also get formatted output.

logging.basicConfig(
    level=log_level,
    format=log_format,
    handlers=[logging.StreamHandler()] # Keep terminal output
)
logger = logging.getLogger(__name__) # Get logger for this app.py file
logger.info(f"Flask application logging configured at level: {log_level_str}")

# --- Add File Handler ---
try:
    # Using RotatingFileHandler is good for production to prevent log files from growing indefinitely
    # It will create up to `backupCount` files, each `maxBytes` in size.
    file_handler = RotatingFileHandler(
        LOG_FILE_PATH,
        maxBytes=1024 * 1024 * 5,  # 5 MB per file
        backupCount=5              # Keep 5 backup files
    )
    file_handler.setFormatter(logging.Formatter(log_format))
    file_handler.setLevel(log_level) # Set the level for this handler

    # Add the file handler to the root logger so all loggers inherit it
    logging.getLogger('').addHandler(file_handler)
    logger.info(f"Successfully configured file logging to: {LOG_FILE_PATH}")

except Exception as e:
    logger.error(f"Failed to configure file logging to {LOG_FILE_PATH}: {e}", exc_info=True)
logger = logging.getLogger(__name__) # Get logger specifically for this app.py file
logger.info(f"Flask application logging configured at level: {log_level_str}")
# --- End Configure Logging ---

# --- App Configuration (Secrets, JWT, Cache) ---
logger.info("Configuring Flask app settings...")
# Secret key for Flask sessions, flash messages, etc.
# IMPORTANT: Set a strong, unique secret key in your environment for production!
app.secret_key = os.environ.get('FLASK_SECRET_KEY')
if not app.secret_key:
    logger.warning("FLASK_SECRET_KEY not set in environment. Using an insecure default key for development.")
    app.secret_key = 'dev-secret-key-please-change-me'

# JWT Configuration
jwt_secret = os.environ.get('JWT_SECRET_KEY')
if not jwt_secret:
    logger.error("FATAL: JWT_SECRET_KEY environment variable not set!")
    logger.warning("Using an insecure default JWT_SECRET_KEY. SET THIS IN YOUR ENVIRONMENT!")
    jwt_secret = 'default-jwt-secret-key-please-change-me'
app.config["JWT_SECRET_KEY"] = jwt_secret
logger.info("JWT Secret Key configured.")
# --- End JWT Config ---

# --- Cache Configuration ---
logger.info("Applying Cache configuration...")
# Define cache object globally in this module's scope, initially None
cache = None
try:
    # Read cache settings from environment variables or use defaults
    app.config['CACHE_TYPE'] = os.environ.get('CACHE_TYPE', 'SimpleCache')
    app.config['CACHE_DEFAULT_TIMEOUT'] = int(os.environ.get('CACHE_DEFAULT_TIMEOUT', 300))
    logger.info(f"Cache Type set to: {app.config['CACHE_TYPE']}")
    logger.info(f"Cache Default Timeout set to: {app.config['CACHE_DEFAULT_TIMEOUT']}")

    # Specific configuration for Redis if selected
    if app.config['CACHE_TYPE'].lower() == 'rediscache': # Case-insensitive check
        redis_url = os.environ.get('CACHE_REDIS_URL')
        if redis_url:
            app.config['CACHE_REDIS_URL'] = redis_url
            logger.info(f"Using Redis Cache with URL from environment: {redis_url}")
        else:
            # Default Redis URL if CACHE_REDIS_URL is not set but type is RedisCache
            app.config['CACHE_REDIS_URL'] = 'redis://localhost:6379/0'
            logger.warning("CACHE_TYPE is RedisCache but CACHE_REDIS_URL not set, using default redis://localhost:6379/0.")
    elif app.config['CACHE_TYPE'].lower() == 'simplecache': # Case-insensitive check
         logger.info("Using SimpleCache (in-memory). Suitable for development/single worker.")
    else:
         # Add support for other types like MemcachedCache if needed
         logger.warning(f"Unknown or unsupported CACHE_TYPE: {app.config['CACHE_TYPE']}. Caching might not work correctly.")

    # Initialize Cache AFTER setting app.config
    # This step registers the cache with the app instance
    
    config = {
             "DEBUG": True,          # some Flask specific configs
             "CACHE_TYPE": "RedisCache",  # Flask-Caching related configs
             "CACHE_DEFAULT_TIMEOUT": 300,
             "CACHE_REDIS_URL": "redis://localhost:6379/0"  
             }

    # tell Flask to use the above defined config
    app.config.from_mapping(config)
    cache = Cache(app)
    logger.info("Flask-Caching initialized successfully.")

except ImportError:
    logger.error("Flask-Caching is not installed (ImportError). Caching disabled. Run: pip install Flask-Caching")
    # cache remains None
except Exception as e:
    logger.error(f"Failed to initialize Flask-Caching: {e}", exc_info=True)
    # cache remains None if initialization fails
# --- End Cache Configuration ---

# --- Initialize Other Extensions ---
# IMPORTANT: Initialize extensions AFTER app and config are set, but BEFORE blueprints are registered
logger.info("Initializing Other Extensions (JWT, CORS)...")
try:
    jwt = JWTManager(app)
    logger.info("Flask-JWT-Extended initialized.")
except Exception as e:
     logger.error(f"Failed to initialize JWTManager: {e}", exc_info=True)

# CORS Configuration
# Read allowed origins from environment variable, split by comma, strip whitespace
cors_origins_str = os.environ.get("CORS_ORIGINS", "*")
print(cors_origins_str)
cors_origins = [origin.strip() for origin in cors_origins_str.split(',')]
print("*******CORS ORIGINS*********",cors_origins)
logger.info(f"Configuring CORS for origins: {cors_origins}")
try:
    CORS(app,
         resources={
             # Apply CORS generally to /api/* routes
             r"/api/*": {
                 "origins": cors_origins, # Use the list directly
                 "methods": ["GET", "POST", "OPTIONS", "PUT", "DELETE"],
                 "allow_headers": ["Content-Type", "Authorization", "X-Requested-With"],
                 "supports_credentials": True,
                 "expose_headers": ["Content-Type", "X-CSRFToken"],
                 "max_age": 600
             }
         },
        # Optionally enable automatic handling of OPTIONS requests
        automatic_options=True
    )
    logger.info("Flask-CORS initialized.")
    app.config['CORS_ORIGINS'] = cors_origins
except Exception as e:
    logger.error(f"Failed to initialize Flask-CORS: {e}", exc_info=True)

# Flask-Admin initialization (if used)
# try:
#     from app.admin import init_admin
#     init_admin(app)
#     logger.info("Flask-Admin initialized.")
# except ImportError:
#      logger.info("Flask-Admin module not found, skipping initialization.")
# except Exception as e:
#     logger.error(f"Failed to initialize Flask-Admin: {e}", exc_info=True)
# --- End Initialize Extensions ---


# --- Import and Register Blueprints ---
# Import blueprints AFTER app and extensions are initialized to avoid circular dependencies
# and ensure extensions are available if blueprints need them during import time (though accessing via current_app is better)
logger.info("Importing and registering blueprints...")
try:
    from app.api.webhook import webhook as webhook_blueprint
    from app.api.custom_llm import custom_llm as custom_llm_blueprint
    # Import other blueprints here

    app.register_blueprint(webhook_blueprint, url_prefix='/api/webhook')
    app.register_blueprint(custom_llm_blueprint, url_prefix='/api/custom_llm')
    # Register other blueprints here

    logger.info("Registered blueprints: webhook, custom_llm")
except NameError as ne:
     # This usually means the import failed silently earlier
     logger.error(f"Failed to register blueprints because they were likely not imported successfully: {ne}", exc_info=True)
except Exception as e:
    logger.error(f"Failed to register blueprints: {e}", exc_info=True)
# --- End Register Blueprints ---


# ------------------------------
# Define Global Routes (if any)
# ------------------------------
@app.route('/')
def index():
    """Health check endpoint."""
    logger.debug("Health check endpoint '/' accessed.")
    return jsonify({"message": "Server is running..."})


@app.route('/endpoints')
def list_endpoints():
    """Lists all registered API endpoints for debugging."""
    output = []
    try:
        for rule in app.url_map.iter_rules():
            # Filter out static and internal Flask/extension routes
            if rule.endpoint and rule.endpoint != 'static' and not rule.endpoint.startswith(('_', 'admin.')):
                methods = ','.join(sorted(rule.methods))
                output.append({
                    "endpoint": str(rule),
                    "methods": methods,
                    "function": rule.endpoint
                })
        logger.debug("Endpoints list endpoint '/endpoints' accessed.")
        # Sort for consistent output
        return jsonify({"endpoints": sorted(output, key=lambda x: x['endpoint'])})
    except Exception as e:
        logger.error(f"Error generating endpoints list: {e}", exc_info=True)
        return jsonify({"error": "Could not retrieve endpoints"}), 500


# ------------------------------
# Run the Application
# ------------------------------
if __name__ == '__main__':
    # Get host, port, and debug mode from environment variables
    port = int(os.getenv('PORT', 5000)) # Changed default port to 3000
    # Use FLASK_DEBUG env var standard practice (set to '1' or 'True' for debug)
    debug_mode = os.environ.get('FLASK_DEBUG', '1').lower() in ['true', '1', 't']
    host = os.environ.get('127.0.0.1', '0.0.0.0') # Listen on all interfaces

    logger.info("--- Starting Flask Development Server ---")
    logger.info(f"Host:         {host}")
    logger.info(f"Port:         {port}")
    logger.info(f"Debug Mode:   {debug_mode}")
    logger.info(f"Cache Type:   {app.config.get('CACHE_TYPE', 'Not Set')}")
    logger.info(f"JWT Secret:   {'SET' if app.config.get('JWT_SECRET_KEY') else 'NOT SET'}") # Don't log the actual key
    logger.info(f"CORS Origins: {app.config.get('CORS_ORIGINS', 'Not Set')}") # CORS isn't stored directly in app.config this way
    logger.info(f"CACHE_REDIS_URL: {app.config.get('CACHE_REDIS_URL', 'Not Set')}")
    logger.info("Note: Use a production WSGI server (Gunicorn, Waitress) in production.")
    logger.info("--- Server Ready ---")

    # Run the Flask development server
    # use_reloader=debug_mode enables auto-reload on code changes when debug is True
    app.run(host=host, port=port, debug=debug_mode, use_reloader=debug_mode)