from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
import json

# Add the directory containing code_1.py to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from code_1 import GitHubRepoExplorer

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

@app.route('/explore_repository', methods=['POST'])
def explore_repository():
    try:
        # Get data from request
        data = request.json
        repo_url = data.get('repo_url')
        github_token = data.get('github_token')

        # Validate inputs
        if not repo_url or not github_token:
            return jsonify({
                'error': 'Repository URL and GitHub Token are required'
            }), 400

        # Extract owner and repo name from URL
        url_parts = repo_url.rstrip('/').split('/')
        repo_name = f"{url_parts[-2]}/{url_parts[-1]}"

        # Initialize explorer
        explorer = GitHubRepoExplorer(github_token)

        # Fetch repository
        repo = explorer.github_client.get_repo(repo_name)

        # Explore repository contents
        report = explorer.explore_repository_contents(repo)

        return jsonify({
            'repository': repo_name,
            'contents': report['contents']
        })

    except Exception as e:
        return jsonify({
            'error': str(e)
        }), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)