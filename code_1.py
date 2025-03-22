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
        Initialize GitHub Repository Explorer
        
        :param github_token: GitHub Personal Access Token
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
    
    def run(self):
        """
        Main execution method
        """
        # Select repository
        repo = self.interactive_repo_selection()
        if not repo:
            print("❌ Repository selection cancelled.")
            return
        
        # Explore repository contents
        report = self.explore_repository_contents(repo)
        if not report:
            print("❌ Could not explore repository contents.")
            return
        
        # Interactive file exploration
        self.interactive_file_selection(repo, report)

def main():
    # GitHub token from environment or user input
    github_token = os.getenv('GITHUB_TOKEN') or input("Enter GitHub Personal Access Token: ")
    
    # Initialize and run explorer
    explorer = GitHubRepoExplorer(github_token)
    explorer.run()

if __name__ == '__main__':
    main()
