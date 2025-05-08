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
import base64
from urllib.parse import urlparse

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

        # Enhanced Branch and Contributor Retrieval
        branches_data = []
        try:
            # Fetch all branches
            branches = repo.get_branches()
            
            for branch in branches:
                branch_data = {
                    'name': branch.name,
                    'commit': branch.commit.sha,
                    'protected': branch.protected,
                    'contributors': []
                }
                
                # Fetch contributors for the entire repository
                try:
                    # Get contributors for the entire repository
                    contributors = list(repo.get_contributors())
                    
                    # Filter contributors based on branch commits (if possible)
                    branch_contributors = [
                        {
                            'login': contributor.login,
                            'name': contributor.name,
                            'avatar_url': contributor.avatar_url,
                            'contributions': contributor.contributions
                        } for contributor in contributors
                        # Optional: Add more sophisticated branch filtering if needed
                    ]
                    branch_data['contributors'] = branch_contributors
                except Exception as contrib_error:
                    logger.warning(f"Could not fetch contributors for branch {branch.name}: {contrib_error}")
                
                branches_data.append(branch_data)
        
        except Exception as branch_error:
            logger.error(f"Error fetching branches: {branch_error}")
        
        # Fetch organization-level contributors
        org_contributors = []
        try:
            if repo.organization:
                # Fetch top contributors across all repositories in the organization
                org_contributors = [
                    {
                        'login': contributor.login,
                        'name': contributor.name,
                        'avatar_url': contributor.avatar_url,
                        'total_contributions': contributor.contributions
                    } 
                    for contributor in repo.organization.get_members()
                ]
        except Exception as org_contrib_error:
            logger.warning(f"Could not fetch organization contributors: {org_contrib_error}")
        
        # Calculate request processing time
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        logger.info(f"Request processed in {processing_time} seconds")

        # Update response data
        response_data = {
            'status': 'success',
            'repository': repo.full_name,
            'organization': repo.organization.login if repo.organization else None,
            'branches': branches_data,
            'organization_contributors': org_contributors,
            'contents': report['contents'],
            'processing_time': processing_time
        }
        
        return jsonify(response_data)

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

@app.route('/explore_branch_files', methods=['POST'])
def explore_branch_files():
    try:
        data = request.json
        repo_url = data.get('repo_url', '')
        
        # Enhanced logging
        logger.info(f"Attempting to explore repository: {repo_url}")
        
        # Handle different URL formats
        if repo_url.startswith('@'):
            repo_url = repo_url[1:]
        
        # Normalize URL parsing
        if repo_url.startswith('https://github.com/'):
            path_parts = repo_url.replace('https://github.com/', '').split('/')
        else:
            path_parts = repo_url.split('/')
        
        # Validate repository path
        if len(path_parts) < 2:
            logger.error(f"Invalid repository URL format: {repo_url}")
            return jsonify({
                'error': 'Invalid repository URL',
                'details': f'Could not parse: {repo_url}'
            }), 400
        
        # Correct repository name extraction
        if 'backend_kodkarta' in path_parts:
            organization = 'kodkarta'
            repository = 'backend_kodkarta'
        else:
            organization = path_parts[0]
            repository = path_parts[1]
        
        # Extract branch if specified
        branch = data.get('branch', 'main')
        if len(path_parts) > 2:
            branch = path_parts[3] if path_parts[2] == 'tree' else branch
        
        # Fallback branch names
        alternative_branches = ['main', 'master', 'develop', 'development']
        
        # Use PyGithub to fetch repository contents
        g = Github(os.getenv('GITHUB_TOKEN'))
        
        # Comprehensive repository validation
        try:
            # Check if the repository exists
            try:
                repo = g.get_repo(f"{organization}/{repository}")
            except Exception as repo_error:
                logger.error(f"Repository not found: {organization}/{repository}")
                logger.error(f"Detailed error: {str(repo_error)}")
                
                # Try searching for similar repositories
                try:
                    search_results = g.search_repositories(f"org:{organization} {repository}")
                    similar_repos = list(search_results)
                    
                    if similar_repos:
                        logger.info(f"Found similar repositories: {[repo.full_name for repo in similar_repos]}")
                        return jsonify({
                            'error': 'Repository Not Found',
                            'similar_repositories': [repo.full_name for repo in similar_repos]
                        }), 404
                except Exception as search_error:
                    logger.error(f"Repository search error: {search_error}")
                
                return jsonify({
                    'error': 'Repository Not Found',
                    'details': str(repo_error)
                }), 404
        
        except Exception as validation_error:
            logger.error(f"Repository validation error: {validation_error}")
            return jsonify({
                'error': 'Repository Validation Failed',
                'details': str(validation_error)
            }), 500
        
        # Try fetching branch contents
        branch_contents = None
        found_branch = None
        
        for potential_branch in [branch] + alternative_branches:
            try:
                branch_contents = repo.get_contents("", ref=potential_branch)
                found_branch = potential_branch
                break
            except Exception as branch_error:
                logger.warning(f"Could not fetch contents for branch {potential_branch}")
        
        if not branch_contents:
            logger.error(f"Could not fetch contents for any branch in {repo.full_name}")
            return jsonify({
                'error': 'No Accessible Branches',
                'details': f'Could not access contents for repository {repo.full_name}'
            }), 404
        
        # Process and return file information
        files = []
        for content in branch_contents:
            file_info = {
                'name': content.name,
                'path': content.path,
                'type': 'directory' if content.type == 'dir' else 'file',
                'size': content.size if content.type == 'file' else 0,
                'branch': found_branch
            }
            files.append(file_info)
        
        return jsonify({
            'files': files,
            'branch': found_branch,
            'repository': repo.full_name
        })
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return jsonify({
            'error': 'Unexpected Error',
            'details': str(e)
        }), 500

@app.route('/preview_file', methods=['POST'])
def preview_file():
    try:
        data = request.json
        file_path = data.get('file_path')
        
        # Fetch file content
        g = Github(os.getenv('GITHUB_TOKEN'))
        repo = g.get_repo(f"{organization}/{repository}")
        
        file_content = repo.get_contents(file_path)
        decoded_content = base64.b64decode(file_content.content).decode('utf-8')
        
        return jsonify(decoded_content)
    
    except Exception as e:
        logger.error(f"File preview error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_organization_details', methods=['POST'])
def get_organization_details():
    try:
        data = request.json
        organization_name = data.get('organization')
        
        # Use PyGithub to fetch organization details
        g = Github(os.getenv('GITHUB_TOKEN'))
        org = g.get_organization(organization_name)
        
        # Collect organization-level details
        details = {
            'repo_count': org.total_private_repos + org.total_public_repos,
            'total_contributors': len(list(org.get_members())),
            # Add more details as needed
        }
        
        return jsonify(details)
    
    except Exception as e:
        logger.error(f"Organization details error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/get_repository_details', methods=['POST'])
def get_repository_details():
    try:
        data = request.json
        repository_name = data.get('repository')
        
        # Use PyGithub to fetch repository details
        g = Github(os.getenv('GITHUB_TOKEN'))
        repo = g.get_repo(repository_name)
        
        # Collect repository-level details
        details = {
            'languages': {lang: percent for lang, percent in repo.get_languages().items()},
            'stars': repo.stargazers_count,
            'forks': repo.forks_count,
            # Add more details as needed
        }
        
        return jsonify(details)
    
    except Exception as e:
        logger.error(f"Repository details error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/explore_branch_assets', methods=['POST'])
def explore_branch_assets():
    try:
        data = request.json
        repo_url = data.get('repo_url')
        branch = data.get('branch')
        github_token = data.get('github_token')

        # Initialize GitHub client
        g = Github(github_token)
        
        # Parse repository details
        repo_parts = repo_url.replace('https://github.com/', '').split('/')
        organization = repo_parts[0]
        repository = repo_parts[1]
        
        # Get repository
        repo = g.get_repo(f"{organization}/{repository}")
        
        # Discover branch-specific assets
        branch_assets = {
            'branch_name': branch,
            'github_actions': discover_github_actions(repo, branch),
            'databases': discover_databases(repo, branch),
            'cloud_projects': discover_cloud_projects(repo, branch)
        }
        
        return jsonify(branch_assets)
    
    except Exception as e:
        logger.error(f"Error exploring branch assets: {e}")
        return jsonify({
            'error': 'Failed to explore branch assets',
            'details': str(e)
        }), 500

def discover_github_actions(repo, branch):
    try:
        # Look for workflow files in .github/workflows directory
        workflows = []
        try:
            workflow_files = repo.get_contents(".github/workflows", ref=branch)
            for workflow in workflow_files:
                workflows.append({
                    'name': workflow.name,
                    'type': 'GitHub Action',
                    'path': workflow.path
                })
        except Exception as e:
            logger.warning(f"Could not fetch GitHub Actions: {e}")
        
        return workflows
    except Exception as e:
        logger.error(f"Error in discover_github_actions: {e}")
        return []

def discover_databases(repo, branch):
    try:
        # Look for database configuration files
        database_configs = []
        database_patterns = [
            'database.yml', 'database.json', 
            'db.json', 'db.yml', 
            'config/database.py', 
            'prisma/schema.prisma',
            'migrations/'
        ]
        
        for pattern in database_patterns:
            try:
                db_files = repo.get_contents(pattern, ref=branch)
                for db_file in db_files:
                    database_configs.append({
                        'name': db_file.name,
                        'type': 'Database Configuration',
                        'path': db_file.path
                    })
            except Exception:
                pass
        
        return database_configs
    except Exception as e:
        logger.error(f"Error in discover_databases: {e}")
        return []

def discover_cloud_projects(repo, branch):
    try:
        # Look for cloud provider configuration files
        cloud_configs = []
        cloud_patterns = [
            # Terraform
            '*.tf', 
            # AWS CloudFormation
            '*.yaml', '*.yml', 
            # Azure Resource Manager
            '*.json',
            # Kubernetes
            'k8s/', 'kubernetes/', 
            # Serverless Framework
            'serverless.yml'
        ]
        
        for pattern in cloud_patterns:
            try:
                cloud_files = repo.get_contents(pattern, ref=branch)
                for cloud_file in cloud_files:
                    cloud_configs.append({
                        'name': cloud_file.name,
                        'provider': infer_cloud_provider(cloud_file.name),
                        'path': cloud_file.path
                    })
            except Exception:
                pass
        
        return cloud_configs
    except Exception as e:
        logger.error(f"Error in discover_cloud_projects: {e}")
        return []

def infer_cloud_provider(filename):
    providers_map = {
        'aws': ['aws', 'amazon', 'cloudformation'],
        'azure': ['azure', 'microsoft'],
        'gcp': ['gcp', 'google', 'googlecloud'],
        'terraform': ['terraform', 'tf'],
        'kubernetes': ['k8s', 'kubernetes']
    }
    
    filename_lower = filename.lower()
    
    for provider, keywords in providers_map.items():
        if any(keyword in filename_lower for keyword in keywords):
            return provider
    
    return 'Unknown'

# Server Configuration
if __name__ == '__main__':
    free_port = find_free_port()
    print(f"Using available port: {free_port}")
    app.run(
        debug=True, 
        host='0.0.0.0',  
        port=free_port
    )