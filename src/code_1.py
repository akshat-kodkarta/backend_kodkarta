import os
import re
import ast
import json
import base64
import hashlib
import yaml
import glob
import time
import asyncio
import datetime
from typing import List, Dict, Any, Tuple, Optional
from pathlib import Path
import requests
from dotenv import load_dotenv
from github import Github

try:
    import graphviz
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

try:
    from github import Github, RateLimitExceededException
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False

# Load environment variables from .env file
load_dotenv()

# Retrieve GitHub token
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

# If token not found, prompt user
if not GITHUB_TOKEN:
    GITHUB_TOKEN = input("Please enter your GitHub Personal Access Token: ")
    
    # Optionally, save to .env for future use
    with open('.env', 'a') as f:
        f.write(f"\nGITHUB_TOKEN={GITHUB_TOKEN}")

class GitHubRepoExplorer:
    def __init__(self, github_token):
        """
        Initialize GitHub Repository Explorer with enhanced branch exploration
        """
        self.github_token = github_token
        self.github_client = Github(github_token)
        self.headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github.v3+json'
        }
    
    def interactive_repo_selection(self):
        """
        Interactively select a GitHub repository
        
        :return: Selected repository object
        """
        while True:
            try:
                # Prompt for repository
                repo_input = input("Enter GitHub repository (format: owner/repo-name): ").strip()
                
                # Validate input format
                if '/' not in repo_input:
                    print("❌ Invalid repository format. Use 'owner/repo-name'")
                    continue
                
                # Fetch repository
                repo = self.github_client.get_repo(repo_input)
                
                # Confirm repository selection
                print("\n🔍 Repository Details:")
                print(f"Name: {repo.full_name}")
                print(f"Description: {repo.description or 'No description'}")
                print(f"Language: {repo.language or 'Not specified'}")
                print(f"Stars: {repo.stargazers_count}")
                print(f"Forks: {repo.forks_count}")
                
                # Confirm selection
                confirm = input("\nConfirm repository? (y/n): ").lower()
                if confirm == 'y':
                    return repo
                
            except Exception as e:
                print(f"❌ Error accessing repository: {e}")
                retry = input("Try again? (y/n): ").lower()
                if retry != 'y':
                    return None
    
    def explore_repository_contents(self, repo):
        """
        Explore and categorize repository contents
        
        :param repo: GitHub repository object
        :return: Detailed repository contents report
        """
        try:
            # Initialize report structure
            report = {
                'repository': repo.full_name,
                'contents': {
                    'directories': [],
                    'files': [],
                    'file_types': {}
                }
            }
            
            # Get repository contents
            contents = repo.get_contents("")
            
            while contents:
                content = contents.pop(0)
                
                if content.type == 'dir':
                    # Add directory to report
                    report['contents']['directories'].append(content.path)
                    
                    # Recursively get directory contents
                    try:
                        contents.extend(repo.get_contents(content.path))
                    except Exception as dir_error:
                        print(f"⚠️ Could not access directory {content.path}: {dir_error}")
                
                elif content.type == 'file':
                    # Categorize file
                    file_extension = os.path.splitext(content.name)[1]
                    file_type = file_extension.lstrip('.')
                    
                    # Track file types
                    report['contents']['file_types'][file_type] = \
                        report['contents']['file_types'].get(file_type, 0) + 1
                    
                    # Add file details
                    file_info = {
                        'name': content.name,
                        'path': content.path,
                        'type': file_type,
                        'size': content.size
                    }
                    report['contents']['files'].append(file_info)
            
            return report
        
        except Exception as e:
            print(f"❌ Error exploring repository: {e}")
            return None
    
    def interactive_file_selection(self, repo, report):
        """
        Interactively select and explore files
        
        :param repo: GitHub repository object
        :param report: Repository contents report
        """
        while True:
            print("\n📂 Repository File Explorer")
            print("File Types Found:")
            for file_type, count in report['contents']['file_types'].items():
                print(f"- {file_type.upper()}: {count} files")
            
            # Prompt for file type selection
            file_type = input("\nEnter file type to explore (or 'q' to quit): ").lower()
            
            if file_type == 'q':
                break
            
            # Filter files by selected type
            matching_files = [
                file for file in report['contents']['files'] 
                if file['type'].lower() == file_type
            ]
            
            if not matching_files:
                print(f"❌ No files found with type: {file_type}")
                continue
            
            # Display matching files
            print(f"\n📄 {file_type.upper()} Files:")
            for i, file in enumerate(matching_files, 1):
                print(f"{i}. {file['name']} (Size: {file['size']} bytes)")
            
            # Select specific file
            try:
                file_index = int(input("\nEnter file number to view contents (or 0 to go back): ")) - 1
                
                if file_index == -1:
                    continue
                
                selected_file = matching_files[file_index]
                
                # Fetch file contents
                file_content = repo.get_contents(selected_file['path'])
                
                # Decode file content (for text files)
                try:
                    decoded_content = file_content.decoded_content.decode('utf-8')
                    print(f"\n📝 Contents of {selected_file['name']}:")
                    print(decoded_content[:1000] + "..." if len(decoded_content) > 1000 else decoded_content)
                except UnicodeDecodeError:
                    print("⚠️ Unable to decode file contents (possibly binary file)")
                
            except (ValueError, IndexError):
                print("❌ Invalid selection")
    
    def explore_repository_branches(self, repo):
        """
        Comprehensive branch exploration for a repository
        
        :param repo: GitHub repository object
        :return: Detailed branch information
        """
        try:
            # Initialize branch report
            branch_report = {
                'repository': repo.full_name,
                'total_branches': 0,
                'branches': []
            }

            # Fetch all branches
            branches = repo.get_branches()

            for branch in branches:
                # Detailed branch information
                branch_info = {
                    'name': branch.name,
                    'commit': {
                        'sha': branch.commit.sha,
                        'date': branch.commit.commit.author.date.isoformat(),
                        'message': branch.commit.commit.message[:100]  # Truncate long messages
                    },
                    'protected': branch.protected,
                    'protection_details': self._get_branch_protection_details(repo, branch.name) if branch.protected else None
                }
                
                branch_report['branches'].append(branch_info)
                branch_report['total_branches'] += 1

            return branch_report

        except Exception as e:
            print(f"❌ Error exploring repository branches: {e}")
            return None

    def _get_branch_protection_details(self, repo, branch_name):
        """
        Retrieve detailed branch protection rules
        
        :param repo: GitHub repository object
        :param branch_name: Name of the branch
        :return: Branch protection details
        """
        try:
            protection = repo.get_branch_protection(branch_name)
            return {
                'required_status_checks': protection.required_status_checks.contexts if protection.required_status_checks else None,
                'enforce_admins': protection.enforce_admins.enabled,
                'required_pull_request_reviews': {
                    'required_approving_review_count': protection.required_pull_request_reviews.required_approving_review_count if protection.required_pull_request_reviews else None,
                    'dismiss_stale_reviews': protection.required_pull_request_reviews.dismiss_stale_reviews if protection.required_pull_request_reviews else None
                },
                'restrictions': {
                    'users': [user.login for user in protection.restrictions.users] if protection.restrictions else None,
                    'teams': [team.name for team in protection.restrictions.teams] if protection.restrictions else None
                }
            }
        except Exception as e:
            print(f"⚠️ Could not fetch branch protection details: {e}")
            return None

    def explore_user_repositories(self, username=None):
        """
        Explore all repositories for a user or the authenticated user
        
        :param username: Optional username to explore (defaults to authenticated user)
        :return: Comprehensive repository exploration report
        """
        try:
            # Use provided username or get authenticated user
            if username:
                user = self.github_client.get_user(username)
            else:
                user = self.github_client.get_user()

            # Initialize repository report
            repo_report = {
                'username': user.login,
                'total_repositories': 0,
                'repositories': []
            }

            # Fetch user repositories
            repositories = user.get_repos()

            for repo in repositories:
                # Detailed repository information
                repo_info = {
                    'name': repo.full_name,
                    'description': repo.description,
                    'language': repo.language,
                    'stars': repo.stargazers_count,
                    'forks': repo.forks_count,
                    'created_at': repo.created_at.isoformat(),
                    'updated_at': repo.updated_at.isoformat(),
                    'visibility': repo.visibility,
                    'default_branch': repo.default_branch,
                    'branches': self.explore_repository_branches(repo)
                }
                
                repo_report['repositories'].append(repo_info)
                repo_report['total_repositories'] += 1

            return repo_report

        except Exception as e:
            print(f"❌ Error exploring user repositories: {e}")
            return None

    def interactive_user_exploration(self):
        """
        Interactive exploration of user's GitHub repositories and branches
        """
        try:
            # Prompt for username (optional)
            username_input = input("Enter GitHub username (press Enter for authenticated user): ").strip()
            
            # Explore repositories
            if username_input:
                report = self.explore_user_repositories(username_input)
            else:
                report = self.explore_user_repositories()

            if not report:
                print("❌ No repositories found or exploration failed.")
                return

            # Display repository summary
            print("\n🔍 Repository Exploration Summary")
            print(f"Username: {report['username']}")
            print(f"Total Repositories: {report['total_repositories']}")

            # Interactive repository selection
            for i, repo in enumerate(report['repositories'], 1):
                print(f"\n{i}. {repo['name']} ({repo['visibility']})")
                print(f"   Language: {repo['language'] or 'Not specified'}")
                print(f"   Stars: {repo['stars']} | Forks: {repo['forks']}")
                print(f"   Default Branch: {repo['default_branch']}")

            # Select repository for detailed branch exploration
            try:
                repo_index = int(input("\nSelect repository number for branch details (0 to exit): ")) - 1
                
                if 0 <= repo_index < len(report['repositories']):
                    selected_repo = report['repositories'][repo_index]
                    print(f"\n📂 Branch Details for {selected_repo['name']}")
                    
                    branches = selected_repo['branches']['branches']
                    for branch in branches:
                        print(f"\nBranch: {branch['name']}")
                        print(f"Last Commit: {branch['commit']['date']}")
                        print(f"Commit Message: {branch['commit']['message']}")
                        print(f"Protected: {branch['protected']}")
                        
                        if branch['protection_details']:
                            print("🔒 Branch Protection Details:")
                            print(json.dumps(branch['protection_details'], indent=2))
                
            except (ValueError, IndexError):
                print("❌ Invalid selection")

        except Exception as e:
            print(f"❌ Interactive exploration error: {e}")

    def run(self):
        """
        Enhanced main execution method with user repository exploration
        """
        print("🚀 GitHub Repository Explorer")
        print("1. Explore Single Repository")
        print("2. Explore User Repositories")
        
        choice = input("Select exploration mode (1/2): ").strip()
        
        if choice == '1':
            # Existing single repository exploration
            repo = self.interactive_repo_selection()
            if repo:
                report = self.explore_repository_contents(repo)
                if report:
                    self.interactive_file_selection(repo, report)
        elif choice == '2':
            # New user repository exploration
            self.interactive_user_exploration()
        else:
            print("❌ Invalid selection")

def main():
    # GitHub token from environment or user input
    github_token = os.getenv('GITHUB_TOKEN') or input("Enter GitHub Personal Access Token: ")
    
    # Initialize and run explorer
    explorer = GitHubRepoExplorer(github_token)
    explorer.run()

if __name__ == '__main__':
    main()
