document.addEventListener('DOMContentLoaded', function() {
    const repoForm = document.getElementById('repo-form');
    const repoUrlInput = document.getElementById('repo-url');
    const githubTokenInput = document.getElementById('github-token');
    const resultContainer = document.getElementById('result-container');
    const resultOutput = document.getElementById('result-output');
    
    // Enhanced Form Validation
    repoForm.addEventListener('submit', function(event) {
        event.preventDefault();
        event.stopPropagation();

        // Validate form
        if (repoForm.checkValidity()) {
            const repoUrl = repoUrlInput.value.trim();
            const githubToken = githubTokenInput.value.trim();

            // Perform fetch only if inputs are valid
            exploreRepository(repoUrl, githubToken);
        }

        repoForm.classList.add('was-validated');
    }, false);

    function exploreRepository(repoUrl, githubToken) {
        // Show loading state
        resultOutput.innerHTML = '<div class="text-center">🔄 Exploring repository...</div>';

        fetch('/explore_repository', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repo_url: repoUrl,
                github_token: githubToken
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Debug logging
            console.log('Repository Exploration Data:', data);
            
            // Log branches and contributors
            if (data.branches) {
                console.log('Branches:', data.branches);
                data.branches.forEach(branch => {
                    console.log(`Branch: ${branch.name}`);
                    console.log('Contributors:', branch.contributors);
                });
            }

            // Existing success handling
            if (data.status === 'success') {
                resultOutput.innerHTML = `
                    <h4>Repository: ${data.repository}</h4>
                    <p>Processing Time: ${data.processing_time.toFixed(2)} seconds</p>
                    <h5>Branches Summary:</h5>
                    <pre>${JSON.stringify(data.branches, null, 2)}</pre>
                `;
                
                // Create Asset Connection Map
                createAssetConnectionMap(data);
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            console.error('Exploration Error:', error);
            resultOutput.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
        });
    }
});

// Add this function to the existing repository_explorer.js file
function createAssetConnectionMap(repositoryData) {
    console.log('Repository Data:', repositoryData);

    // Clear previous visualization
    d3.select("#asset-map-container").selectAll("*").remove();

    // Prepare data for visualization
    const nodes = [];
    const links = [];

    // Root node (Organization)
    const rootNode = {
        id: 0,
        name: repositoryData.organization || 'GitHub Organization',
        type: 'organization',
        group: 'organization',
        size: 70,
        clickable: true,
        onClick: () => {
            // Organization-level actions
            showOrganizationDetails(repositoryData.organization);
        }
    };
    nodes.push(rootNode);

    // Collect organization-level contributors
    const orgContributors = repositoryData.organization_contributors || [];
    orgContributors.forEach((contributor, contribIndex) => {
        const orgContributorNode = {
            id: `org_contrib_${contribIndex}`,
            name: contributor.login || contributor.name,
            username: contributor.login,  // Explicitly capture username
            type: 'organization_contributor',
            group: 'contributor',
            size: 25,
            avatar: contributor.avatar_url,
            contributions: contributor.total_contributions || 0
        };
        nodes.push(orgContributorNode);

        // Link organization to contributor
        links.push({
            source: 0,
            target: orgContributorNode.id,
            type: 'org_contributor_link',
            value: orgContributorNode.contributions
        });
    });

    // Repository as a secondary node
    const repoNode = {
        id: 1,
        name: repositoryData.repository || 'Repository',
        type: 'repository',
        group: 'repository',
        size: 50,
        clickable: true,
        onClick: () => {
            // Repository-level actions
            showRepositoryDetails(repositoryData.repository);
        }
    };
    nodes.push(repoNode);

    // Create link between organization and repository
    links.push({
        source: 0,
        target: 1,
        type: 'org_repo_link',
        value: 2
    });

    // Process branches
    const branches = repositoryData.branches || [];
    branches.forEach((branch, branchIndex) => {
        // Create branch node
        const branchNode = {
            id: branchIndex + 100,
            name: branch.name,
            type: 'branch',
            group: 'branch',
            size: 35,
            protected: branch.protected,
            clickable: true,
            onClick: async () => {
                try {
                    // Fetch files for the selected branch
                    const files = await fetchBranchFiles(
                        repositoryData, 
                        branch.name
                    );

                    // Update file list sidebar
                    updateFileSidebar(files, branch.name);

                    // Highlight selected branch
                    highlightSelectedBranch(branchNode);
                } catch (error) {
                    console.error('Error in branch click handler:', error);
                }
            }
        };
        nodes.push(branchNode);

        // Link repository to branch
        links.push({
            source: 1,
            target: branchNode.id,
            type: 'repo_branch_link',
            value: 1
        });

        // Process contributors for this branch
        const contributors = branch.contributors || [];
        contributors.forEach((contributor, contribIndex) => {
            // Create contributor node
            const contributorNode = {
                id: `branch_contrib_${branchIndex}_${contribIndex}`,
                name: contributor.name || contributor.login,
                username: contributor.login,
                type: 'branch_contributor',
                group: 'contributor',
                size: 20,
                avatar: contributor.avatar_url,
                contributions: contributor.contributions || 0,
                branch: branch.name,
                clickable: true,
                onClick: () => {
                    // Contributor-level actions
                    showContributorDetails(contributor);
                }
            };
            nodes.push(contributorNode);

            // Link branch to contributor
            links.push({
                source: branchNode.id,
                target: contributorNode.id,
                type: 'branch_contributor_link',
                value: contributor.contributions || 1
            });
        });
    });

    // Visualization setup
    const container = document.getElementById('asset-map-container');
    const width = container.clientWidth || 800;
    const height = container.clientHeight || 600;

    const svg = d3.select("#asset-map-container")
        .append("svg")
        .attr("width", "100%")
        .attr("height", "100%")
        .attr("viewBox", `0 0 ${width} ${height}`);

    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain([
            'organization', 'repository', 'branch', 
            'organization_contributor', 'branch_contributor', 
            'python', 'javascript', 'config', 'documentation', 'other'
        ])
        .range([
            "#3366cc",   // organization
            "#ff9900",   // repository
            "#4B8BBE",   // branch
            "#28a745",   // org contributor
            "#17a2b8",   // branch contributor
            "#4B8BBE",   // python
            "#F0DB4F",   // javascript
            "#6A5ACD",   // config
            "#17a2b8",   // documentation
            "#6c757d"    // other
        ]);

    // Force simulation
    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id).distance(150))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide", d3.forceCollide(30));

    // Create links
    const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .enter().append("line")
        .attr("stroke", d => colorScale(d.type))
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", d => Math.sqrt(d.value));

    // Create nodes with pattern for contributors
    const node = svg.append("g")
        .selectAll("g")
        .data(nodes)
        .enter().append("g")
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    // Circles for nodes
    const circles = node.append("circle")
        .attr("r", d => d.size)
        .attr("fill", d => colorScale(d.group))
        .attr("stroke", d => {
            // Highlight protected branches
            if (d.type === 'branch' && d.protected) return "#dc3545";
            return "#fff";
        })
        .attr("stroke-width", d => {
            // Thicker stroke for protected branches
            return d.type === 'branch' && d.protected ? 3 : 1.5;
        })
        .style("cursor", d => d.clickable ? "pointer" : "default")
        .on("click", (event, d) => {
            if (d.clickable && d.onClick) {
                d.onClick();
            }
        });

    // Add avatar images for contributors
    const contributorImages = node.filter(d => d.type === 'organization_contributor' || d.type === 'branch_contributor')
        .append("image")
        .attr("xlink:href", d => d.avatar)
        .attr("x", d => -d.size/2)
        .attr("y", d => -d.size/2)
        .attr("width", d => d.size)
        .attr("height", d => d.size)
        .attr("clip-path", "circle()");

    // Add username labels for contributors
    const usernameLabels = node.filter(d => d.username)
        .append("text")
        .text(d => `@${d.username}`)
        .attr("font-size", 8)
        .attr("text-anchor", "middle")
        .attr("dy", d => d.size + 10)
        .attr("fill", "#333");

    // Tooltip
    const tooltip = d3.select("body")
        .append("div")
        .attr("class", "tooltip")
        .style("opacity", 0);

    node.on("mouseover", (event, d) => {
        tooltip.transition()
            .duration(200)
            .style("opacity", .9);
        
        let tooltipContent = `<strong>${d.name}</strong><br>Type: ${d.type}`;
        
        if (d.username) {
            tooltipContent += `<br>Username: @${d.username}`;
        }
        
        tooltipContent += `<br>Type: ${d.type}`;
        
        if (d.type === 'organization_contributor' || d.type === 'branch_contributor') {
            tooltipContent += `<br>Contributions: ${d.contributions}`;
            if (d.type === 'branch_contributor') {
                tooltipContent += `<br>Branch: ${d.branch}`;
            }
        }
        
        if (d.type === 'branch') {
            tooltipContent += `<br>Protected: ${d.protected ? 'Yes' : 'No'}`;
        }
        
        tooltip.html(tooltipContent)
        .style("left", (event.pageX + 10) + "px")
        .style("top", (event.pageY - 28) + "px");
    })
    .on("mouseout", () => {
        tooltip.transition()
            .duration(500)
            .style("opacity", 0);
    });

    // Add labels
    const label = svg.append("g")
        .selectAll("text")
        .data(nodes)
        .enter().append("text")
        .text(d => d.name)
        .attr("font-size", 10)
        .attr("dx", 12)
        .attr("dy", ".35em")
        .attr("fill", "#333");

    // Simulation tick event
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("transform", d => `translate(${d.x},${d.y})`);

        label
            .attr("x", d => d.x)
            .attr("y", d => d.y);
    });

    // Drag functions
    function dragstarted(event, d) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        d.fx = d.x;
        d.fy = d.y;
    }

    function dragged(event, d) {
        d.fx = event.x;
        d.fy = event.y;
    }

    function dragended(event, d) {
        if (!event.active) simulation.alphaTarget(0);
        d.fx = null;
        d.fy = null;
    }

    // New helper functions for node interactions
    function showOrganizationDetails(organizationName) {
        const detailsModal = document.getElementById('details-modal');
        detailsModal.innerHTML = `
            <div class="modal-header">
                <h5>Organization Details: ${organizationName}</h5>
            </div>
            <div class="modal-body">
                <!-- Add organization-specific details -->
                <p>Fetching organization details...</p>
            </div>
        `;
        detailsModal.style.display = 'block';

        // Fetch and populate organization details
        fetch('/get_organization_details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ organization: organizationName })
        })
        .then(response => response.json())
        .then(details => {
            // Update modal with fetched details
            detailsModal.querySelector('.modal-body').innerHTML = `
                <h6>Repositories: ${details.repo_count}</h6>
                <h6>Total Contributors: ${details.total_contributors}</h6>
                <!-- Add more details as needed -->
            `;
        })
        .catch(error => {
            console.error('Error fetching organization details:', error);
            detailsModal.querySelector('.modal-body').innerHTML = `
                <p>Failed to fetch organization details</p>
            `;
        });
    }

    function showRepositoryDetails(repositoryName) {
        const detailsModal = document.getElementById('details-modal');
        detailsModal.innerHTML = `
            <div class="modal-header">
                <h5>Repository Details: ${repositoryName}</h5>
            </div>
            <div class="modal-body">
                <p>Fetching repository details...</p>
            </div>
        `;
        detailsModal.style.display = 'block';

        // Fetch and populate repository details
        fetch('/get_repository_details', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ repository: repositoryName })
        })
        .then(response => response.json())
        .then(details => {
            // Update modal with fetched details
            detailsModal.querySelector('.modal-body').innerHTML = `
                <h6>Language Distribution:</h6>
                <ul>
                    ${Object.entries(details.languages).map(([lang, percent]) => 
                        `<li>${lang}: ${percent}%</li>`
                    ).join('')}
                </ul>
                <h6>Repository Stats:</h6>
                <p>Stars: ${details.stars}</p>
                <p>Forks: ${details.forks}</p>
            `;
        })
        .catch(error => {
            console.error('Error fetching repository details:', error);
            detailsModal.querySelector('.modal-body').innerHTML = `
                <p>Failed to fetch repository details</p>
            `;
        });
    }

    function showContributorDetails(contributor) {
        const detailsModal = document.getElementById('details-modal');
        detailsModal.innerHTML = `
            <div class="modal-header">
                <h5>Contributor Details: ${contributor.name || contributor.login}</h5>
            </div>
            <div class="modal-body">
                <img src="${contributor.avatar_url}" alt="Avatar" class="contributor-avatar">
                <p>Username: ${contributor.login}</p>
                <p>Contributions: ${contributor.contributions}</p>
            </div>
        `;
        detailsModal.style.display = 'block';
    }

    function highlightSelectedBranch(branchNode) {
        // Remove previous highlights
        d3.selectAll('circle')
            .attr('stroke', d => {
                if (d.type === 'branch' && d.protected) return "#dc3545";
                return "#fff";
            });

        // Highlight selected branch
        d3.selectAll('circle')
            .filter(d => d.id === branchNode.id)
            .attr('stroke', '#28a745')
            .attr('stroke-width', 4);
    }
}

// New function to fetch branch files
async function fetchBranchFiles(repositoryData, branchName) {
    try {
        // Handle different repository URL formats
        let repoUrl = repositoryData.repository_url || 
                      `https://github.com/${repositoryData.organization}/${repositoryData.repository}`;
        
        // Remove '@' if present and handle special cases
        if (repoUrl.startsWith('@')) {
            repoUrl = repoUrl.substring(1);
        }
        
        // Normalize URL for backend processing
        if (repoUrl.includes('backend_kodkarta')) {
            repoUrl = 'https://github.com/kodkarta/backend_kodkarta';
        }
        
        const response = await fetch('/explore_branch_files', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                repo_url: repoUrl,
                branch: branchName
            })
        });

        const data = await response.json();

        if (!response.ok) {
            // Handle specific error scenarios
            if (data.similar_repositories) {
                // Show similar repositories suggestion
                const errorModal = document.getElementById('error-modal');
                errorModal.innerHTML = `
                    <div class="modal-header">
                        <h5>Repository Not Found</h5>
                    </div>
                    <div class="modal-body">
                        <p>The repository was not found. Did you mean one of these?</p>
                        <ul>
                            ${data.similar_repositories.map(repo => `<li>${repo}</li>`).join('')}
                        </ul>
                    </div>
                `;
                errorModal.style.display = 'block';
            }

            throw new Error(data.error || 'Failed to fetch branch files');
        }

        return data.files;
    } catch (error) {
        console.error('Error fetching branch files:', error);
        
        // Show user-friendly error
        const errorModal = document.getElementById('error-modal');
        errorModal.innerHTML = `
            <div class="modal-header">
                <h5>Error Fetching Branch Files</h5>
            </div>
            <div class="modal-body">
                <p>${error.message}</p>
                <p>Please check the repository URL and try again.</p>
            </div>
        `;
        errorModal.style.display = 'block';

        throw error;
    }
}

function updateFileSidebar(files, branchName) {
    const fileList = document.getElementById('file-list');
    const currentBranchName = document.getElementById('current-branch-name');
    
    // Update branch name
    currentBranchName.textContent = branchName;
    
    // Clear previous files
    fileList.innerHTML = '';
    
    // Group files by type (directories first, then files)
    const directories = files.filter(file => file.type === 'directory');
    const regularFiles = files.filter(file => file.type === 'file');
    
    // Combine and sort files
    const sortedFiles = [...directories, ...regularFiles];
    
    // Create file list items
    sortedFiles.forEach(file => {
        const listItem = document.createElement('li');
        listItem.classList.add('file-item');
        listItem.dataset.path = file.path;
        listItem.dataset.type = file.type;
        
        // Determine icon based on file type
        const icon = getFileIcon(file.type, file.name);
        
        listItem.innerHTML = `
            <span class="file-item-icon">${icon}</span>
            <span class="file-item-name">${file.name}</span>
            ${file.type === 'file' ? `<span class="file-item-size">${formatFileSize(file.size)}</span>` : ''}
        `;
        
        // Add click event for file preview
        listItem.addEventListener('click', () => previewFile(file));
        
        fileList.appendChild(listItem);
    });
}

function getFileIcon(fileType, fileName) {
    // Comprehensive file type icon mapping
    const iconMap = {
        'directory': '📁',
        'file': '📄',
        'python': '🐍',
        'javascript': '📜',
        'typescript': '🔷',
        'markdown': '📝',
        'json': '🗂️',
        'yaml': '📋',
        'html': '🌐',
        'css': '🎨'
    };
    
    // Determine icon based on file extension
    if (fileType === 'file') {
        const extension = fileName.split('.').pop().toLowerCase();
        return iconMap[extension] || iconMap['file'];
    }
    
    return iconMap[fileType] || '📄';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${parseFloat((bytes / Math.pow(k, i)).toFixed(2))} ${sizes[i]}`;
}

function previewFile(file) {
    // Implement file preview logic
    fetch('/preview_file', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
            file_path: file.path,
            repository: currentRepository,  // Global variable to track current repository
            branch: currentBranch  // Global variable to track current branch
        })
    })
    .then(response => response.json())
    .then(fileContent => {
        // Display file content in a modal or preview area
        const previewModal = document.getElementById('file-preview-modal');
        previewModal.innerHTML = `
            <div class="modal-header">
                <h5>File Preview: ${file.path}</h5>
                <button type="button" class="btn-close" onclick="closePreviewModal()"></button>
            </div>
            <div class="modal-body">
                <pre class="language-${getLanguageFromExtension(file.name)}">${escapeHtml(fileContent)}</pre>
            </div>
        `;
        previewModal.style.display = 'block';
    })
    .catch(error => {
        console.error('File preview error:', error);
        alert('Could not preview file');
    });
}

function getLanguageFromExtension(fileName) {
    const extensionMap = {
        'py': 'python',
        'js': 'javascript',
        'ts': 'typescript',
        'html': 'html',
        'css': 'css',
        'json': 'json',
        'yaml': 'yaml',
        'yml': 'yaml'
    };
    
    const extension = fileName.split('.').pop().toLowerCase();
    return extensionMap[extension] || 'text';
}

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

function closePreviewModal() {
    const previewModal = document.getElementById('file-preview-modal');
    previewModal.style.display = 'none';
}

// Helper function to determine asset group
function getAssetGroup(item) {
    const fileName = item.name || item.path || '';
    const fileExtension = fileName.split('.').pop().toLowerCase();
    
    const assetGroups = {
        'py': 'python',
        'js': 'javascript',
        'json': 'config',
        'yaml': 'config',
        'yml': 'config',
        'md': 'documentation',
        'txt': 'text'
    };
    
    return assetGroups[fileExtension] || 'other';
}

class RepositoryExplorer {
    constructor(githubClient) {
        this.githubClient = githubClient;
        this.scanQueue = [];
        this.scanResults = {};
    }

    async exploreOrganization(organizationName) {
        const repositories = await this.fetchRepositories(organizationName);
        
        for (const repo of repositories) {
            await this.queueRepositoryScan(repo);
        }
    }

    async queueRepositoryScan(repository) {
        const scanTasks = [
            this.scanRepositoryStructure(repository),
            this.scanRepositoryDependencies(repository),
            this.scanRepositorySecrets(repository),
            this.visualizeRepositoryInsights(repository)
        ];

        const results = await Promise.all(scanTasks);
        this.updateVisualization(results);
    }

    async visualizeRepositoryInsights(repository) {
        // Create interactive D3.js visualization
        createAssetConnectionMap({
            organization: repository.organization,
            repository: repository.name,
            branches: await this.getBranchContributors(repository),
            contents: await this.getRepositoryContents(repository)
        });
    }
}
