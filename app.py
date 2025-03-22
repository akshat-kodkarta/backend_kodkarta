import os
import sys
import json
import logging
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import traceback
from github import Github
import time
import socket

# Configure Flask App
app = Flask(__name__, 
            static_folder='static',     # Serve static files from 'static' directory
            static_url_path='/static',  # URL prefix for static files
            template_folder='templates' # Look for templates in 'templates' directory
)

# Add project root and src to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src'))

# Detailed CORS Configuration
CORS(app, resources={
    r"/*": {  # Apply to all routes
        "origins": [
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "*"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": [
            "Content-Type", 
            "Authorization", 
            "Access-Control-Allow-Credentials"
        ],
        "supports_credentials": True
    }
})

# Logging Configuration
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('github_explorer.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Import from src directory
from src.code_1 import GitHubRepoExplorer

# Custom JSON encoder to handle non-serializable objects
class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        try:
            return super().default(obj)
        except TypeError:
            return str(obj)

app.json_encoder = CustomJSONEncoder

# CORS Debugging Middleware
@app.before_request
def log_request_info():
    logger.info(f"Incoming Request: {request.method} {request.path}")
    logger.info(f"Request Headers: {request.headers}")

# Root Route to Serve index.html
@app.route('/')
def index():
    """
    Serve the main index.html file
    """
    logger.info("Serving main index page")
    return render_template('index.html')

# Favicon Route to prevent 404 errors
@app.route('/favicon.ico')
def favicon():
    """
    Handle favicon requests to prevent 404 errors
    """
    logger.info("Favicon request received")
    return '', 204  # No content response

@app.route('/asset_map')
def asset_map():
    """Serve the asset map page"""
    return render_template('asset_map.html')

@app.route('/explore_repository', methods=['POST'])
def explore_repository():
    try:
        # Comprehensive Request Logging
        logger.info("🚀 Received Repository Exploration Request")
        logger.info(f"📋 Request Headers: {request.headers}")
        
        # Validate Request Content Type
        if not request.is_json:
            logger.error("❌ Invalid Request: Not JSON")
            return jsonify({
                'error': 'Invalid Request',
                'details': 'Content-Type must be application/json'
            }), 400

        # Detailed Request Parsing
        try:
            data = request.get_json()
        except Exception as parsing_error:
            logger.error(f"🔍 Request Parsing Error: {parsing_error}")
            return jsonify({
                'error': 'Request Parsing Failed',
                'details': str(parsing_error)
            }), 400

        # Comprehensive Input Validation
        repo_url = data.get('repo_url')
        github_token = data.get('github_token')

        validation_errors = []
        if not repo_url:
            validation_errors.append("Repository URL is missing")
        if not github_token:
            validation_errors.append("GitHub Token is missing")

        if validation_errors:
            logger.error(f"❌ Validation Errors: {validation_errors}")
            return jsonify({
                'error': 'Validation Failed',
                'details': validation_errors
            }), 400

        # Detailed Logging
        logger.info(f"🔗 Repository URL: {repo_url}")
        logger.info(f"🔑 Token Length: {len(github_token)}")

        # Validate GitHub Token
        try:
            g = Github(github_token)
            user = g.get_user()
            logger.info(f"Token validated for user: {user.login}")
        except Exception as token_error:
            logger.error(f"Token Validation Failed: {token_error}")
            return jsonify({
                'error': 'GitHub Token Validation Failed',
                'details': str(token_error)
            }), 401

        # Start timing the request
        start_time = datetime.now()
        
        # Detailed input validation with logging
        validation_errors = []
        if not repo_url:
            validation_errors.append("Repository URL is missing")
            logger.error("Repository URL validation failed")
        
        if not github_token:
            validation_errors.append("GitHub Token is missing")
            logger.error("GitHub Token validation failed")
        
        if validation_errors:
            return jsonify({
                'error': 'Validation Failed',
                'details': validation_errors,
                'status': 'failed'
            }), 400

        # Log sanitized repository information
        logger.info(f"Processing repository: {repo_url}")

        # Extract owner and repo name from URL
        url_parts = repo_url.rstrip('/').split('/')
        repo_name = f"{url_parts[-2]}/{url_parts[-1]}"
        logger.info(f"Extracted Repository Name: {repo_name}")

        # Initialize explorer with detailed logging
        try:
            explorer = GitHubRepoExplorer(github_token)
            logger.info("GitHub Explorer initialized successfully")
        except Exception as init_error:
            logger.error(f"Explorer initialization failed: {init_error}")
            return jsonify({
                'error': 'GitHub Explorer Initialization Failed',
                'details': str(init_error),
                'status': 'failed'
            }), 500

        # Fetch repository with error handling
        try:
            repo = explorer.github_client.get_repo(repo_name)
            logger.info(f"Repository {repo_name} fetched successfully")
        except Exception as repo_error:
            logger.error(f"Repository fetch failed: {repo_error}")
            return jsonify({
                'error': 'Repository Fetch Failed',
                'details': str(repo_error),
                'status': 'failed'
            }), 404

        # Explore repository contents
        try:
            report = explorer.explore_repository_contents(repo)
            logger.info("Repository contents explored successfully")
        except Exception as explore_error:
            logger.error(f"Repository exploration failed: {explore_error}")
            return jsonify({
                'error': 'Repository Exploration Failed',
                'details': str(explore_error),
                'status': 'failed'
            }), 500

        # Calculate request processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        logger.info(f"Request processed in {processing_time} seconds")

        return jsonify({
            'repository': repo_name,
            'contents': report['contents'],
            'processing_time': processing_time,
            'status': 'success'
        })

    except Exception as e:
        # Global Error Handling
        logger.error(f"🚨 Unhandled Server Error: {e}")
        logger.error(traceback.format_exc())
        
        return jsonify({
            'error': 'Unexpected Server Error',
            'details': str(e)
        }), 500

@app.errorhandler(Exception)
def handle_global_exception(e):
    """
    Global error handler for unhandled exceptions
    """
    logger.critical(f"Unhandled Global Exception: {e}")
    logger.critical(traceback.format_exc())
    
    return jsonify({
        'error': 'Critical Server Error',
        'details': str(e),
        'status': 'failed'
    }), 500

# Potential Authentication Problems
def check_github_token(token):
    try:
        g = Github(token)
        user = g.get_user()
        print(f"Token Details:")
        print(f"Username: {user.login}")
        print(f"Email: {user.email}")
        print(f"Company: {user.company}")
        return True
    except Exception as e:
        print(f"Token Validation Failed: {e}")
        return False

def handle_rate_limit(github_client):
    rate_limit = github_client.get_rate_limit()
    print(f"Rate Limit:")
    print(f"Remaining: {rate_limit.core.remaining}")
    print(f"Reset Time: {rate_limit.core.reset}")
    
    if rate_limit.core.remaining == 0:
        wait_time = (rate_limit.core.reset - datetime.now()).total_seconds()
        print(f"Rate limit exceeded. Waiting {wait_time} seconds.")
        time.sleep(wait_time)

def validate_github_token(token):
    try:
        from github import Github
        g = Github(token)
        
        # Comprehensive token check
        user = g.get_user()
        print("Token Validation Details:")
        print(f"Username: {user.login}")
        print(f"Email: {user.email}")
        print(f"Company: {user.company}")
        
        # Check rate limit
        rate_limit = g.get_rate_limit()
        print(f"Rate Limit Remaining: {rate_limit.core.remaining}")
        print(f"Rate Limit Reset Time: {rate_limit.core.reset}")
        
        return True
    except Exception as e:
        print(f"Token Validation Failed: {e}")
        return False

# Custom CORS Error Handler
@app.errorhandler(Exception)
def handle_cors_error(e):
    logger.error(f"CORS Error: {e}")
    return jsonify({
        "error": "CORS Configuration Error",
        "details": str(e)
    }), 500

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

# Optional: Add explicit route for serving CSS
@app.route('/static/css/<path:filename>')
def serve_css(filename):
    return send_from_directory('static/css', filename)

# Server Configuration
if __name__ == '__main__':
    free_port = find_free_port()
    print(f"Using available port: {free_port}")
    app.run(
        debug=True, 
        host='0.0.0.0',  
        port=free_port
    )