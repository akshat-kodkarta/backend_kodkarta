# GitHub Repository Explorer

## Overview

GitHub Repository Explorer is a web application that allows users to analyze and visualize GitHub repositories. It provides insights into repository structure, branches, contributors, and file relationships through an interactive visualization.

## Features

- **Repository Analysis**: Explore any public GitHub repository by providing its URL
- **Branch Visualization**: View all branches and their relationships
- **Contributor Insights**: See who contributed to each branch
- **File Structure**: Browse files within each branch
- **Interactive Map**: Visual representation of repository components and their relationships
- **Rate Limit Management**: Smart handling of GitHub API rate limits

## How It Works

### Authentication

The application requires a GitHub Personal Access Token to authenticate API requests. This increases the rate limit from 60 requests/hour (unauthenticated) to 5,000 requests/hour (authenticated).

### Repository Exploration Process

1. **Initial Request**: When a user submits a repository URL and GitHub token, the application sends a request to the backend.

2. **Asynchronous Processing**: The backend processes the request asynchronously to avoid blocking the UI:
   - Fetches repository metadata
   - Retrieves branches and their details
   - Collects contributor information
   - Analyzes file structure

3. **Hierarchical Scanning**:
   - First level: Organization and repositories
   - Second level: Repository structure and branches
   - Third level: Files, code, and dependencies
   - Fourth level: Detailed code analysis and secrets scanning

4. **Rate Limit Management**:
   - Tracks remaining API requests
   - Implements intelligent backoff strategy when approaching limits
   - Prioritizes critical requests over less important ones
   - Caches results to minimize duplicate requests

5. **Visualization**:
   - Creates an interactive D3.js visualization of the repository
   - Displays branches as nodes connected to the main repository
   - Shows contributors connected to their respective branches
   - Provides a file browser for exploring repository contents

### Technical Implementation

#### Frontend

- **HTML/CSS/JavaScript**: Responsive UI with modern design principles
- **Bootstrap**: For layout and basic components
- **D3.js**: For interactive repository visualization
- **Fetch API**: For asynchronous communication with the backend

#### Backend

- **Python/Flask**: Server-side processing and API handling
- **PyGithub**: GitHub API client for Python
- **Asynchronous Processing**: Background tasks for handling long-running operations
- **Caching**: Stores results to minimize API calls

## Detailed Setup Guide

### Prerequisites

- Python 3.8 or higher
- Git
- Internet connection
- GitHub account (for creating a Personal Access Token)

### Step 1: Clone the Repository

```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate
```

### Step 2: Install Dependencies

The project requires several Python packages. Install them using pip:

```bash
pip install -r requirements.txt
```

The `requirements.txt` file contains:

```
# Web Framework
flask==2.0.1
flask-cors==3.0.10

# GitHub Interaction
PyGithub==1.55
requests==2.26.0

# Environment Management
python-dotenv==0.19.0

# Data Processing
pyyaml==6.0
typing-extensions==4.5.0

# Optional: For advanced async processing
asyncio==3.4.3

# Optional: For logging
logging==0.5.1.2
```

### Step 3: Create a GitHub Personal Access Token

1. Log in to your GitHub account
2. Go to **Settings** > **Developer settings** > **Personal access tokens** > **Tokens (classic)**
3. Click **Generate new token** > **Generate new token (classic)**
4. Give your token a descriptive name (e.g., "Repository Explorer")
5. Select the following scopes:
   - `repo` (Full control of private repositories)
   - `read:org` (Read-only access to organization membership)
   - `user:email` (Access user email addresses)
6. Click **Generate token**
7. **IMPORTANT**: Copy your token immediately and store it securely. GitHub will only show it once!

### Step 4: Run the Application

```bash
python app.py
```

The application will start and be available at `http://localhost:5000` in your web browser.

### Step 5: Using the Application

1. Open your web browser and navigate to `http://localhost:5000`
2. You'll see the GitHub Repository Explorer interface with two input fields:
   - **GitHub Repository URL**: Enter the full URL of the repository you want to explore (e.g., `https://github.com/facebook/react`)
   - **GitHub Personal Access Token**: Paste your GitHub token here

3. Click the **Explore Repository** button to start the analysis
4. The application will:
   - Connect to GitHub using your token
   - Fetch repository data
   - Process the information
   - Display the results in the visualization panel

5. Once loaded, you can:
   - View the repository structure
   - Click on branches to see their files
   - Explore contributor information
   - Navigate through the file structure
   - View the relationships between different components

### Troubleshooting

- **Rate Limit Exceeded**: If you see this error, wait for your rate limit to reset (usually 1 hour) or use a different token
- **Repository Not Found**: Verify the repository URL is correct and publicly accessible
- **Token Authentication Failed**: Ensure your token is valid and has the required permissions
- **Application Not Starting**: Check that all dependencies are installed correctly

## Rate Limit Handling

The application implements a sophisticated approach to handle GitHub API rate limits:

1. **Prioritized Scanning**: Critical paths are scanned first, with less important data fetched later
2. **Backoff Strategy**: When rate limits are approached, the application implements exponential backoff
3. **Hierarchical Processing**: Data is processed based on hierarchy level:
   - Level 1: Organization and repositories (minimal API calls)
   - Level 2: Repository structure and branches (moderate API calls)
   - Level 3: Files and code (higher API usage)
   - Level 4: Detailed analysis (highest API usage)
4. **Background Processing**: Lower priority scans happen asynchronously in the background
5. **Rate Limit Monitoring**: Continuous tracking of remaining API requests

## Usage Guidelines

1. **Use a Personal Access Token**: Always use a GitHub token to increase your rate limit
2. **Start with Smaller Repositories**: Large repositories like React or TensorFlow have thousands of files and will quickly exhaust rate limits
3. **Explore Incrementally**: Start with high-level exploration before diving into specific branches
4. **Be Patient with Large Repositories**: The application implements backoff when rate limits are hit

## Future Improvements

- Implement persistent caching to further reduce API calls
- Add repository comparison features
- Enhance visualization with more metrics and insights
- Implement webhook support for real-time updates
- Add support for organization-wide analysis

## Technical Requirements

- Modern web browser with JavaScript enabled
- GitHub Personal Access Token with appropriate permissions
- Internet connection to access GitHub API

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.





