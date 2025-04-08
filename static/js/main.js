document.addEventListener('DOMContentLoaded', function() {
    const connectBtn = document.getElementById('connectGithubBtn');
    const dropdown = document.getElementById('githubDropdown');
    const cancelBtn = document.getElementById('cancelBtn');
    const submitBtn = document.getElementById('submitBtn');
    const connectState = document.getElementById('connect-state');
    const connectedState = document.getElementById('connected-state');
    const loadingOverlay = document.getElementById('loadingOverlay');
    
    // Check for existing session on page load
    checkForExistingSession();
    
    connectBtn.addEventListener('click', function() {
        dropdown.classList.add('show');
    });

    cancelBtn.addEventListener('click', function() {
        dropdown.classList.remove('show');
    });

    submitBtn.addEventListener('click', async function() {
        const repoUrl = document.getElementById('repo-url').value;
        const accessToken = document.getElementById('access-token').value;
        
        if (!repoUrl || !accessToken) {
            alert('Please fill in all fields');
            return;
        }

        try {
            // Show loading state
            loadingOverlay.style.display = 'flex';
            
            console.log('Submitting repository data...', { repoUrl, accessToken: '***' });
            
            // Make API request to explore repository
            const response = await fetch('/explore_repository', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    repo_url: repoUrl,
                    github_token: accessToken
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || data.details || `HTTP error! status: ${response.status}`);
            }

            console.log('Repository data received:', data); // Debug log

            // Save connection details to localStorage
            saveSession({
                repoUrl,
                accessToken,
                repositoryData: data,
                timestamp: new Date().getTime()
            });

            // Hide connect state and show connected state
            connectState.classList.add('d-none');
            connectedState.classList.remove('d-none');

            // Update repository name
            document.getElementById('repo-name').textContent = repoUrl.split('/').pop();
            
            // Create bottom bar
            createBottomBar();

            // Show loading message for visualization
            updateLoadingMessage('Processing repository data...');

            // Start the async visualization process
            setTimeout(() => {
                initializeAssetMapAsync(data);
            }, 100); // Small delay to allow UI to update

            // Hide the dropdown
            dropdown.classList.remove('show');

        } catch (error) {
            console.error('Error:', error);
            alert('Failed to explore repository: ' + error.message);
            
            // Reset to initial state on error
            connectState.classList.remove('d-none');
            connectedState.classList.add('d-none');
            loadingOverlay.style.display = 'none';
        }
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', function(event) {
        if (!event.target.closest('.connect-github-container')) {
            dropdown.classList.remove('show');
        }
    });

    // Session management functions
    function saveSession(sessionData) {
        // Store session data in localStorage
        localStorage.setItem('githubSessionData', JSON.stringify(sessionData));
        console.log('Session saved to localStorage');
    }

    function clearSession() {
        // Remove session data from localStorage
        localStorage.removeItem('githubSessionData');
        console.log('Session cleared from localStorage');
        
        // Reset UI
        connectState.classList.remove('d-none');
        connectedState.classList.add('d-none');
    }

    function checkForExistingSession() {
        try {
            const sessionData = JSON.parse(localStorage.getItem('githubSessionData'));
            
            if (sessionData && sessionData.repoUrl && sessionData.accessToken && sessionData.repositoryData) {
                console.log('Found existing session, restoring connection...');
                
                // Restore form values
                document.getElementById('repo-url').value = sessionData.repoUrl;
                document.getElementById('access-token').value = sessionData.accessToken;
                
                // Update UI
                connectState.classList.add('d-none');
                connectedState.classList.remove('d-none');
                
                // Create bottom bar once connected
                createBottomBar();
                
                // Update repository name
                document.getElementById('repo-name').textContent = sessionData.repoUrl.split('/').pop();
                
                // Check if session data is still fresh (less than 24 hours old)
                const currentTime = new Date().getTime();
                const sessionAge = currentTime - (sessionData.timestamp || 0);
                const maxSessionAge = 24 * 60 * 60 * 1000; // 24 hours in milliseconds
                
                if (sessionAge > maxSessionAge) {
                    console.log('Session data is stale, refreshing from server...');
                    refreshSessionData(sessionData.repoUrl, sessionData.accessToken);
                } else {
                    console.log('Using cached session data');
                    // Initialize visualization with stored data
                    setTimeout(() => {
                        initializeAssetMapAsync(sessionData.repositoryData);
                    }, 100);
                }
                
                return true;
            }
            
            return false;
        } catch (error) {
            console.error('Error restoring session:', error);
            clearSession();
            return false;
        }
    }

    async function refreshSessionData(repoUrl, accessToken) {
        try {
            // Show loading overlay
            loadingOverlay.style.display = 'flex';
            updateLoadingMessage('Refreshing repository data...');
            
            // Make API request to explore repository
            const response = await fetch('/explore_repository', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    repo_url: repoUrl,
                    github_token: accessToken
                })
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || data.details || `HTTP error! status: ${response.status}`);
            }

            console.log('Repository data refreshed:', data);
            
            // Save updated session data
            saveSession({
                repoUrl,
                accessToken,
                repositoryData: data,
                timestamp: new Date().getTime()
            });
            
            // Initialize visualization with fresh data
            initializeAssetMapAsync(data);
            
        } catch (error) {
            console.error('Error refreshing session data:', error);
            alert('Failed to refresh repository data: ' + error.message);
            
            // Try to use cached data instead
            const sessionData = JSON.parse(localStorage.getItem('githubSessionData'));
            if (sessionData && sessionData.repositoryData) {
                initializeAssetMapAsync(sessionData.repositoryData);
            } else {
                clearSession();
            }
        }
    }

    // Add logout/disconnect button to UI
    addDisconnectButton();
    
    function addDisconnectButton() {
        // Check if the button already exists
        if (document.getElementById('disconnectBtn')) {
            return;
        }
        
        // Create disconnect button
        const disconnectBtn = document.createElement('button');
        disconnectBtn.id = 'disconnectBtn';
        disconnectBtn.className = 'btn btn-outline-danger btn-sm';
        disconnectBtn.innerHTML = 'Disconnect';
        disconnectBtn.style.position = 'absolute';
        disconnectBtn.style.top = '1rem';
        disconnectBtn.style.left = '1rem';
        
        // Add click event
        disconnectBtn.addEventListener('click', function() {
            if (confirm('Are you sure you want to disconnect from this repository?')) {
                clearSession();
                location.reload(); // Reload the page to reset the state
            }
        });
        
        // Add to connected state
        const assetMapContainer = document.querySelector('.asset-map-container');
        assetMapContainer.appendChild(disconnectBtn);
    }
});

// Function to update loading message
function updateLoadingMessage(message) {
    const messageElement = document.querySelector('#loadingOverlay p');
    if (messageElement) {
        messageElement.textContent = message;
    }
}

// Async version of the asset map initialization
async function initializeAssetMapAsync(data) {
    try {
        console.log('Starting async visualization process...');
        
        // Setup the SVG container first
        updateLoadingMessage('Setting up visualization canvas...');
        await sleep(500); // Short delay for UI feedback
        
        const width = document.getElementById('asset-map').offsetWidth;
        const height = document.getElementById('asset-map').offsetHeight;

        // Clear any existing SVG
        d3.select("#asset-map").selectAll("*").remove();

        const svg = d3.select("#asset-map")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        // Create a container for the visualization
        const container = svg.append("g");
        
        // Add zoom behavior
        const zoom = d3.zoom()
            .scaleExtent([0.1, 10])
            .on("zoom", (event) => {
                container.attr("transform", event.transform);
            });

        svg.call(zoom);
        
        // Process organization and branch nodes
        updateLoadingMessage('Processing repository structure...');
        await sleep(700);
        const nodes = await processOrganizationAndBranchesAsync(data);
        
        // Process connections
        updateLoadingMessage('Creating relationship graph...');
        await sleep(500);
        const links = createConnectionLinks(nodes);
        
        // Create simulation
        updateLoadingMessage('Building force-directed graph...');
        await sleep(500);
        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(120))
            .force("charge", d3.forceManyBody().strength(-500))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide().radius(50));

        // Start visualization with animation
        updateLoadingMessage('Rendering visualization...');
        await sleep(700);
        await createOrganizationVisualizationAsync(container, nodes, links, simulation);
        
        // Setup map controls
        updateLoadingMessage('Configuring interactive controls...');
        await sleep(300);
        setupMapControls(svg, zoom);
        
        // Add the components sections to the bottom
        createComponentsSections(data);
        
        console.log('Visualization process complete!');
        
        // Hide loading overlay when done
        loadingOverlay.style.display = 'none';
        
    } catch (error) {
        console.error('Error in visualization process:', error);
        updateLoadingMessage('Error creating visualization: ' + error.message);
        await sleep(1000);
        loadingOverlay.style.display = 'none';
    }
}

// Process organization and branches instead of files
async function processOrganizationAndBranchesAsync(data) {
    // Create central repository node
    const repoNode = { 
        id: "repo",
        name: data.repository || "Repository",
        type: "repository",
        group: "repository",
        size: 40,
        icon: "github"
    };
    
    const nodes = [repoNode];
    
    // Add connected services
    updateLoadingMessage('Adding connected services...');
    
    
    
    // Add branches if available
    if (data.branches) {
        updateLoadingMessage('Processing repository branches...');
        for (const branch of data.branches) {
            nodes.push({
                id: `branch-${branch.name}`,
                name: branch.name,
                type: "branch",
                group: "branch",
                size: 25,
                commitSha: branch.commit
            });
            await sleep(100);
        }
    }
    
    return nodes;
}

// Create links between nodes
function createConnectionLinks(nodes) {
    const links = [];
    
    // Process all non-repository nodes to link them to appropriate parents
    nodes.forEach(node => {
        if (node.id !== "repo") {
            if (node.type === "service") {
                // Service nodes connect to the repository
                links.push({
                    source: "repo",
                    target: node.id,
                    type: node.connection || "Connected to"
                });
            } else if (node.type === "branch") {
                // Branch nodes connect to the repository
                links.push({
                    source: "repo",
                    target: node.id,
                    type: "Branch"
                });
            }
        }
    });
    
    return links;
}

// Create the organization visualization
async function createOrganizationVisualizationAsync(container, nodes, links, simulation) {
    // Create links with animation and labels
    updateLoadingMessage('Creating connections...');
    const linkGroup = container.append("g").attr("class", "links");
    
    const link = linkGroup.selectAll("line")
        .data(links)
        .enter()
        .append("line")
        .style("stroke", "#999")
        .style("stroke-opacity", 0)
        .style("stroke-width", 1);
    
    // Animate links appearing
    link.transition()
        .duration(500)
        .style("stroke-opacity", 0.6);
    
    // Add link labels (for connection types)
    const linkLabels = linkGroup.selectAll(".link-label")
        .data(links)
        .enter()
        .append("text")
        .attr("class", "link-label")
        .style("text-anchor", "middle")
        .style("font-size", "10px")
        .style("font-family", "Arial, sans-serif")
        .style("fill", "#666")
        .style("opacity", 0)
        .text(d => d.type);
    
    linkLabels.transition()
        .duration(500)
        .style("opacity", 1);
    
    await sleep(500);
    
    // Create nodes with icons
    updateLoadingMessage('Creating nodes...');
    const nodeGroup = container.append("g").attr("class", "nodes");
    
    const node = nodeGroup.selectAll(".node")
        .data(nodes)
        .enter()
        .append("g")
        .attr("class", "node")
        .call(drag(simulation));
    
    // Circle for each node
    node.append("circle")
        .attr("r", 0)
        .style("fill", d => getNodeColor(d.group))
        .transition()
        .duration(800)
        .attr("r", d => d.size);
    
    // Icons or text within nodes
    node.append("text")
        .attr("text-anchor", "middle")
        .attr("dominant-baseline", "central")
        .style("font-size", d => d.size * 0.5 + "px")
        .style("font-family", "Arial, sans-serif")
        .style("fill", "white")
        .style("opacity", 0)
        .text(d => getNodeIcon(d))
        .transition()
        .duration(800)
        .style("opacity", 1);
    
    // Node labels
    node.append("text")
        .attr("class", "node-label")
        .attr("text-anchor", "middle")
        .attr("dy", d => d.size + 15)
        .style("font-size", "12px")
        .style("font-family", "Arial, sans-serif")
        .style("fill", "#333")
        .style("opacity", 0)
        .text(d => d.name)
        .transition()
        .duration(500)
        .style("opacity", 1);
    
    await sleep(800);
    
    // Add tooltips
    node.append("title")
        .text(d => `${d.name}\nType: ${d.type}`);
    
    // Update positions on simulation tick
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        // Position link labels
        linkLabels
            .attr("x", d => (d.source.x + d.target.x) / 2)
            .attr("y", d => (d.source.y + d.target.y) / 2 - 5);
        
        node
            .attr("transform", d => `translate(${d.x}, ${d.y})`);
    });
    
    // Let the simulation run for a bit
    updateLoadingMessage('Optimizing layout...');
    simulation.alpha(1).restart();
    
    // Make nodes clickable to show branch details
    node.on("click", (event, d) => {
        if (d.type === "branch") {
            showBranchDetails(d);
        }
    });
    
    // Return a promise that resolves when the simulation has cooled down
    return new Promise(resolve => {
        simulation.on("end", () => {
            resolve();
        });
        
        // Force resolve after a timeout in case simulation doesn't end
        setTimeout(resolve, 3000);
    });
}

// Helper function to get node icon
function getNodeIcon(node) {
    switch (node.icon) {
        case "github": return "";
        case "azure": return "A";
        case "vercel": return "V";
        case "discord": return "D";
        default:
            if (node.type === "branch") return "";
            return "";
    }
}

// Get color based on node group
function getNodeColor(group) {
    const colors = {
        repository: "#333333",
        branch: "#0366d6",
        service: "#5c6bc0",
        azure: "#0078d4",
        vercel: "#000000",
        discord: "#7289da"
    };
    return colors[group] || "#999999";
}

// Function to show branch details
function showBranchDetails(branch) {
    console.log(`Showing details for branch: ${branch.name}`);
    
    // Show the details container
    const detailsContainer = document.getElementById('branch-details-container');
    detailsContainer.classList.remove('d-none');
    
    // Update branch files list
    const filesListEl = document.getElementById('branch-files-list');
    filesListEl.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm" role="status"></div> Loading files...</div>';
    
    // Update contributors list
    const contributorsListEl = document.getElementById('branch-contributors-list');
    contributorsListEl.innerHTML = '<div class="text-center py-3"><div class="spinner-border spinner-border-sm" role="status"></div> Loading contributors...</div>';
    
    // Simulate loading branch files (would be an API call in a real app)
    setTimeout(() => {
        // Populate files list
        filesListEl.innerHTML = `
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>package.json</span>
                <span class="badge bg-primary">JavaScript</span>
            </div>
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>app.py</span>
                <span class="badge bg-success">Python</span>
            </div>
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>requirements.txt</span>
                <span class="badge bg-secondary">Text</span>
            </div>
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>Dockerfile</span>
                <span class="badge bg-danger">Docker</span>
            </div>
            <div class="list-group-item d-flex justify-content-between align-items-center">
                <span>README.md</span>
                <span class="badge bg-info">Markdown</span>
            </div>
        `;
        
        // Populate contributors list
        contributorsListEl.innerHTML = `
            <div class="list-group-item d-flex align-items-center">
                <img src="https://github.com/identicons/user1.png" class="rounded-circle me-3" width="32" height="32">
                <div>
                    <div class="fw-bold">JohnDoe</div>
                    <small class="text-muted">12 contributions</small>
                </div>
            </div>
            <div class="list-group-item d-flex align-items-center">
                <img src="https://github.com/identicons/user2.png" class="rounded-circle me-3" width="32" height="32">
                <div>
                    <div class="fw-bold">JaneSmith</div>
                    <small class="text-muted">8 contributions</small>
                </div>
            </div>
            <div class="list-group-item d-flex align-items-center">
                <img src="https://github.com/identicons/user3.png" class="rounded-circle me-3" width="32" height="32">
                <div>
                    <div class="fw-bold">BobJohnson</div>
                    <small class="text-muted">5 contributions</small>
                </div>
            </div>
        `;
    }, 1500);
}

// Create the components sections at the bottom of the page
function createComponentsSections(data) {
    // Remove existing components container if it exists
    const existingContainer = document.getElementById('components-container');
    if (existingContainer) {
        existingContainer.remove();
    }
    
    // Create a container for the components table
    const componentsContainer = document.createElement('div');
    componentsContainer.id = 'components-container';
    componentsContainer.className = 'mt-4';
    
    // Create a table with 4 columns
    componentsContainer.innerHTML = `
        <div class="components-table-wrapper">
            <table class="components-table">
                <thead>
                    <tr>
                        <th>
                            <div class="table-header">
                                <span>Branch Files</span>
                                <span class="badge bg-primary rounded-circle">&nbsp;</span>
                            </div>
                        </th>
                        <th>
                            <div class="table-header">
                                <span>Contributors</span>
                                <span class="badge bg-info rounded-circle">&nbsp;</span>
                            </div>
                        </th>
                        <th>
                            <div class="table-header">
                                <span>Active Components</span>
                                <span class="badge bg-success rounded-circle">&nbsp;</span>
                            </div>
                        </th>
                        <th>
                            <div class="table-header">
                                <span>Inactive Components</span>
                                <span class="badge bg-danger rounded-circle">&nbsp;</span>
                            </div>
                        </th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>
                            <ul id="files-list" class="component-list">
                                <li class="text-center"><span class="spinner-border spinner-border-sm"></span> Loading files...</li>
                            </ul>
                        </td>
                        <td>
                            <ul id="contributors-list" class="component-list">
                                <li class="text-center"><span class="spinner-border spinner-border-sm"></span> Loading contributors...</li>
                            </ul>
                        </td>
                        <td>
                            <ul id="active-components" class="component-list">
                                <li class="text-center"><span class="spinner-border spinner-border-sm"></span> Loading components...</li>
                            </ul>
                        </td>
                        <td>
                            <ul id="inactive-components" class="component-list">
                                <li class="text-center"><span class="spinner-border spinner-border-sm"></span> Loading components...</li>
                            </ul>
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
    `;
    
    // Add the container to the connected state
    document.getElementById('connected-state').appendChild(componentsContainer);
    
    // Fetch and populate data for each section
    populateComponentsData(data);
}

// Populate the components with data from the GitHub API
async function populateComponentsData(data) {
    try {
        // Populate files list
        populateFilesList(data);
        
        // Populate contributors list
        populateContributorsList(data);
        
        // Populate active and inactive components
        populateComponents(data);
    } catch (error) {
        console.error('Error populating components data:', error);
    }
}

// Populate the files list with actual repository files
function populateFilesList(data) {
    const filesList = document.getElementById('files-list');
    if (!filesList) return;
    
    // Check if we have file data
    if (data.contents && data.contents.files && data.contents.files.length > 0) {
        // Sort files by type/extension
        const sortedFiles = [...data.contents.files].sort((a, b) => {
            const extA = a.name.split('.').pop().toLowerCase();
            const extB = b.name.split('.').pop().toLowerCase();
            return extA.localeCompare(extB);
        });
        
        // Limit to 10 files to avoid overwhelming the UI
        const filesToShow = sortedFiles.slice(0, 10);
        
        let filesHtml = '';
        filesToShow.forEach(file => {
            const extension = file.name.split('.').pop().toLowerCase();
            const fileIcon = getFileIcon(extension);
            
            filesHtml += `
                <li>
                    <a href="#" data-file-path="${file.path}">
                        <span class="file-icon">${fileIcon}</span>
                        <span class="file-name">${file.name}</span>
                        <span class="ms-auto">→</span>
                    </a>
                </li>
            `;
        });
        
        // Add "Show more" if there are more files
        if (data.contents.files.length > 10) {
            filesHtml += `
                <li class="text-center">
                    <a href="#" id="show-more-files" class="btn btn-sm btn-outline-primary">
                        Show ${data.contents.files.length - 10} more files
                    </a>
                </li>
            `;
        }
        
        filesList.innerHTML = filesHtml;
        
        // Add click event listeners for files
        document.querySelectorAll('#files-list a[data-file-path]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const filePath = link.getAttribute('data-file-path');
                showFileDetails(filePath, data);
            });
        });
        
        // Add show more files handler
        const showMoreBtn = document.getElementById('show-more-files');
        if (showMoreBtn) {
            showMoreBtn.addEventListener('click', (e) => {
                e.preventDefault();
                showAllFiles(data.contents.files);
            });
        }
    } else {
        filesList.innerHTML = '<li class="text-center">No files found</li>';
    }
}

// Populate the contributors list with actual repository contributors
function populateContributorsList(data) {
    const contributorsList = document.getElementById('contributors-list');
    if (!contributorsList) return;
    
    let contributors = [];
    
    // Check for organization-level contributors first
    if (data.organization_contributors && data.organization_contributors.length > 0) {
        contributors = data.organization_contributors;
    } 
    // Then check for branch-level contributors as fallback
    else if (data.branches) {
        // Collect unique contributors across all branches
        const uniqueContributors = new Map();
        
        data.branches.forEach(branch => {
            if (branch.contributors) {
                branch.contributors.forEach(contributor => {
                    // Use contributor login as key to avoid duplicates
                    if (!uniqueContributors.has(contributor.login)) {
                        uniqueContributors.set(contributor.login, contributor);
                    } else {
                        // If contributor exists, sum up their contributions
                        const existing = uniqueContributors.get(contributor.login);
                        existing.contributions = (existing.contributions || 0) + (contributor.contributions || 0);
                    }
                });
            }
        });
        
        contributors = Array.from(uniqueContributors.values());
    }
    
    if (contributors.length > 0) {
        // Sort contributors by contribution count (descending)
        contributors.sort((a, b) => (b.contributions || 0) - (a.contributions || 0));
        
        // Limit to 8 top contributors
        const topContributors = contributors.slice(0, 8);
        
        let contributorsHtml = '';
        topContributors.forEach(contributor => {
            contributorsHtml += `
                <li>
                    <a href="#">
                        <img src="${contributor.avatar_url || 'https://github.com/identicons/user.png'}" 
                             class="rounded-circle" width="24" height="24">
                        <span>${contributor.login || contributor.name || 'User'}</span>
                        <span class="ms-auto">${contributor.contributions || 0} →</span>
                    </a>
                </li>
            `;
        });
        
        // Add "Show more" if there are more contributors
        if (contributors.length > 8) {
            contributorsHtml += `
                <li class="text-center">
                    <a href="#" id="show-more-contributors" class="btn btn-sm btn-outline-info">
                        Show ${contributors.length - 8} more contributors
                    </a>
                </li>
            `;
        }
        
        contributorsList.innerHTML = contributorsHtml;
        
        // Add show more contributors handler
        const showMoreBtn = document.getElementById('show-more-contributors');
        if (showMoreBtn) {
            showMoreBtn.addEventListener('click', (e) => {
                e.preventDefault();
                showAllContributors(contributors);
            });
        }
    } else {
        contributorsList.innerHTML = '<li class="text-center">No contributors found</li>';
    }
}

// Populate active and inactive components based on repository data
function populateComponents(data) {
    // For Active Components, we'll use directories from the repository
    populateActiveComponents(data);
    
    // For Inactive Components, we'll use metadata or create dummy data
    populateInactiveComponents(data);
}

// Populate active components with repository directories
function populateActiveComponents(data) {
    const activeComponentsList = document.getElementById('active-components');
    if (!activeComponentsList) return;
    
    if (data.contents && data.contents.directories && data.contents.directories.length > 0) {
        // Get top-level directories
        const topDirs = data.contents.directories.filter(dir => !dir.includes('/') || dir.split('/').length === 1);
        
        // If no top-level dirs, use all dirs
        const directories = topDirs.length > 0 ? topDirs : data.contents.directories.slice(0, 5);
        
        let componentsHtml = '';
        directories.slice(0, 5).forEach(dir => {
            // Extract directory name from path
            const dirName = dir.split('/').pop() || dir;
            
            componentsHtml += `
                <li>
                    <a href="#" data-dir="${dir}">
                        <i class="fas fa-folder"></i>
                        <span>${dirName}</span>
                        <span class="ms-auto">→</span>
                    </a>
                </li>
            `;
        });
        
        activeComponentsList.innerHTML = componentsHtml;
        
        // Add click event listeners
        document.querySelectorAll('#active-components a[data-dir]').forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const dir = link.getAttribute('data-dir');
                showDirectoryFiles(dir, data);
            });
        });
    } else {
        // Create sample components based on file types if directories not available
        const fileTypes = analyzeFileTypes(data);
        
        if (fileTypes.length > 0) {
            let componentsHtml = '';
            fileTypes.slice(0, 5).forEach(type => {
                componentsHtml += `
                    <li>
                        <a href="#" data-type="${type.type}">
                            <i class="fas fa-code-branch"></i>
                            <span>${type.name}</span>
                            <span class="ms-auto">→</span>
                        </a>
                    </li>
                `;
            });
            
            activeComponentsList.innerHTML = componentsHtml;
            
            // Add click event listeners
            document.querySelectorAll('#active-components a[data-type]').forEach(link => {
                link.addEventListener('click', (e) => {
                    e.preventDefault();
                    const type = link.getAttribute('data-type');
                    showFilesByType(type, data);
                });
            });
        } else {
            activeComponentsList.innerHTML = '<li class="text-center">No active components found</li>';
        }
    }
}

// Populate inactive components (could be unused code, deprecated packages, etc.)
function populateInactiveComponents(data) {
    const inactiveComponentsList = document.getElementById('inactive-components');
    if (!inactiveComponentsList) return;
    
    // Check for package dependencies to identify potential inactive components
    let inactiveComponentsData = [];
    
    // Look for package.json, requirements.txt, etc.
    if (data.contents && data.contents.files) {
        const packageFile = data.contents.files.find(file => 
            file.name === 'package.json' || 
            file.name === 'requirements.txt' || 
            file.name === 'yarn.lock' || 
            file.name === 'composer.json'
        );
        
        if (packageFile) {
            // We found a dependency file - in a real app we would parse it
            // Here we'll just show placeholder content
            inactiveComponentsData = [
                { name: "Legacy Module", type: "deprecated", icon: "fas fa-archive" },
                { name: "Outdated Package", type: "outdated", icon: "fas fa-history" },
                { name: "Unused Dependency", type: "unused", icon: "fas fa-unlink" },
                { name: "Security Risk", type: "security", icon: "fas fa-shield-alt" },
                { name: "Duplicate Code", type: "duplicate", icon: "fas fa-copy" }
            ];
        }
    }
    
    if (inactiveComponentsData.length > 0) {
        let componentsHtml = '';
        inactiveComponentsData.forEach(component => {
            componentsHtml += `
                <li>
                    <a href="#" data-inactive-type="${component.type}">
                        <i class="${component.icon}"></i>
                        <span>${component.name}</span>
                        <span class="ms-auto">→</span>
                    </a>
                </li>
            `;
        });
        
        inactiveComponentsList.innerHTML = componentsHtml;
    } else {
        inactiveComponentsList.innerHTML = '<li class="text-center">No inactive components detected</li>';
    }
}

// Helper function to get an icon for a file extension
function getFileIcon(extension) {
    // This could be expanded with more file type icons
    const iconMap = {
        'js': '📄', // JavaScript
        'ts': '📄', // TypeScript
        'py': '🐍', // Python
        'html': '🌐', // HTML
        'css': '🎨', // CSS
        'json': '📋', // JSON
        'md': '📝', // Markdown
        'yml': '⚙️', // YAML
        'yaml': '⚙️', // YAML
        'xml': '📰', // XML
        'sql': '🗄️', // SQL
        'sh': '🔧', // Shell
        'bat': '🔧', // Batch
        'txt': '📄', // Text
        'pdf': '📑', // PDF
        'jpg': '🖼️', // Image
        'jpeg': '🖼️', // Image
        'png': '🖼️', // Image
        'gif': '🖼️', // Image
        'svg': '🖼️', // SVG
        'mp4': '📹', // Video
        'mp3': '🎵', // Audio
        'zip': '📦', // Archive
        'jar': '☕', // Java Archive
        'java': '☕', // Java
        'c': '💻', // C
        'cpp': '💻', // C++
        'h': '💻', // Header file
        'cs': '💻', // C#
        'go': '💻', // Go
        'rs': '💻', // Rust
        'rb': '💎', // Ruby
        'php': '🐘', // PHP
    };
    
    return iconMap[extension] || '📄';
}

// Analyze file types to create component categories
function analyzeFileTypes(data) {
    if (!data.contents || !data.contents.files || data.contents.files.length === 0) {
        return [];
    }
    
    // Count file types
    const typeCounts = {};
    data.contents.files.forEach(file => {
        const ext = file.name.split('.').pop().toLowerCase();
        typeCounts[ext] = (typeCounts[ext] || 0) + 1;
    });
    
    // Group file types into categories
    const categories = [
        { type: 'frontend', name: 'Frontend Components', extensions: ['js', 'jsx', 'ts', 'tsx', 'vue', 'html', 'css', 'scss'] },
        { type: 'backend', name: 'Backend Services', extensions: ['py', 'rb', 'php', 'java', 'go', 'cs', 'js', 'ts'] },
        { type: 'config', name: 'Configuration Files', extensions: ['json', 'yml', 'yaml', 'xml', 'ini', 'toml', 'env'] },
        { type: 'docs', name: 'Documentation', extensions: ['md', 'txt', 'pdf', 'docx'] },
        { type: 'data', name: 'Data Files', extensions: ['csv', 'sql', 'json', 'xml'] }
    ];
    
    // Count files in each category
    const categoryCounts = categories.map(category => {
        const count = category.extensions.reduce((sum, ext) => sum + (typeCounts[ext] || 0), 0);
        return { ...category, count };
    });
    
    // Sort by count (most files first) and return non-empty categories
    return categoryCounts
        .filter(cat => cat.count > 0)
        .sort((a, b) => b.count - a.count);
}

// Show details for a specific file
function showFileDetails(filePath, data) {
    alert(`Viewing file details for: ${filePath}`);
    // In a real implementation, you would make an API call to fetch file contents
    // or open a modal with file details
}

// Show all files in a modal or expanded view
function showAllFiles(files) {
    alert(`Showing all ${files.length} files`);
    // In a real implementation, you would open a modal with all files
}

// Show all contributors in a modal or expanded view
function showAllContributors(contributors) {
    alert(`Showing all ${contributors.length} contributors`);
    // In a real implementation, you would open a modal with all contributors
}

// Show files in a specific directory
function showDirectoryFiles(directory, data) {
    alert(`Showing files in directory: ${directory}`);
    // In a real implementation, you would filter files by directory and display them
}

// Show files of a specific type
function showFilesByType(type, data) {
    alert(`Showing files of type: ${type}`);
    // In a real implementation, you would filter files by type and display them
}

function drag(simulation) {
    function dragstarted(event) {
        if (!event.active) simulation.alphaTarget(0.3).restart();
        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
    }

    function dragged(event) {
        event.subject.fx = event.x;
        event.subject.fy = event.y;
    }

    function dragended(event) {
        if (!event.active) simulation.alphaTarget(0);
        event.subject.fx = null;
        event.subject.fy = null;
    }

    return d3.drag()
        .on("start", dragstarted)
        .on("drag", dragged)
        .on("end", dragended);
}

function setupMapControls(svg, zoom) {
    const zoomIn = document.getElementById('zoomIn');
    const zoomOut = document.getElementById('zoomOut');
    const resetZoom = document.getElementById('resetZoom');
    const filter = document.getElementById('filter');

    if (zoomIn) {
        zoomIn.addEventListener('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 1.5);
        });
    }

    if (zoomOut) {
        zoomOut.addEventListener('click', () => {
            svg.transition().duration(300).call(zoom.scaleBy, 0.75);
        });
    }

    if (resetZoom) {
        resetZoom.addEventListener('click', () => {
            svg.transition().duration(300).call(zoom.transform, d3.zoomIdentity);
        });
    }

    if (filter) {
        filter.addEventListener('change', (event) => {
            filterNodes(event.target.value, svg);
        });
    }
}

function filterNodes(filterValue, svg) {
    const nodes = svg.selectAll("circle");
    const links = svg.selectAll("line");
    const labels = svg.selectAll("text");

    if (filterValue === 'all') {
        nodes.style('opacity', 1);
        links.style('opacity', 0.6);
        labels.style('opacity', 1);
    } else {
        nodes.style('opacity', d => d && d.group === filterValue ? 1 : 0.2);
        links.style('opacity', d => {
            if (!d || !d.source || !d.target) return 0.1;
            const sourceGroup = d.source.group;
            const targetGroup = d.target.group;
            return (sourceGroup === filterValue || targetGroup === filterValue) ? 0.6 : 0.1;
        });
        labels.style('opacity', d => d && d.group === filterValue ? 1 : 0.2);
    }
}

// Helper function for controlled delay
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Add this function to create the bottom bar
function createBottomBar() {
    // Check if bottom bar already exists
    if (document.getElementById('bottom-bar')) {
        return;
    }
    
    // Create bottom bar container
    const bottomBar = document.createElement('div');
    bottomBar.id = 'bottom-bar';
    bottomBar.className = 'bottom-bar';
    
    // Add content to bottom bar
    bottomBar.innerHTML = `
        <div class="bottom-bar-container">
            <div class="bottom-bar-section">
                <span class="status-indicator online"></span>
                <span class="status-text">Connected to GitHub</span>
            </div>
            <div class="bottom-bar-section">
                <span class="bottom-bar-stat">
                    <i class="fas fa-code-branch"></i>
                    <span id="branch-count">0</span> Branches
                </span>
                <span class="bottom-bar-stat">
                    <i class="fas fa-users"></i>
                    <span id="contributor-count">0</span> Contributors
                </span>
                <span class="bottom-bar-stat">
                    <i class="fas fa-file-code"></i>
                    <span id="file-count">0</span> Files
                </span>
            </div>
            <div class="bottom-bar-section">
                <span class="bottom-bar-time">Last updated: <span id="last-updated">Just now</span></span>
            </div>
        </div>
    `;
    
    // Add to document
    document.querySelector('.app-wrapper').appendChild(bottomBar);
    
    // Update bottom bar stats when data is available
    updateBottomBarStats();
}

// Function to update stats in the bottom bar
function updateBottomBarStats() {
    try {
        // Get session data if available
        const sessionData = JSON.parse(localStorage.getItem('githubSessionData'));
        if (!sessionData || !sessionData.repositoryData) return;
        
        const data = sessionData.repositoryData;
        
        // Update branch count
        const branchCount = data.branches ? data.branches.length : 0;
        const branchCountEl = document.getElementById('branch-count');
        if (branchCountEl) branchCountEl.textContent = branchCount;
        
        // Update contributor count
        let contributorCount = 0;
        if (data.organization_contributors) {
            contributorCount = data.organization_contributors.length;
        } else if (data.branches) {
            // Get unique contributors across all branches
            const uniqueContributors = new Set();
            data.branches.forEach(branch => {
                if (branch.contributors) {
                    branch.contributors.forEach(contributor => {
                        uniqueContributors.add(contributor.login);
                    });
                }
            });
            contributorCount = uniqueContributors.size;
        }
        
        const contributorCountEl = document.getElementById('contributor-count');
        if (contributorCountEl) contributorCountEl.textContent = contributorCount;
        
        // Update file count
        const fileCount = data.contents && data.contents.files ? data.contents.files.length : 0;
        const fileCountEl = document.getElementById('file-count');
        if (fileCountEl) fileCountEl.textContent = fileCount;
        
        // Update last updated time
        const lastUpdatedEl = document.getElementById('last-updated');
        if (lastUpdatedEl && sessionData.timestamp) {
            const lastUpdated = new Date(sessionData.timestamp);
            // Format the date: "Today at 14:30" or "Jan 15 at 14:30"
            const today = new Date();
            let timeString;
            
            if (lastUpdated.toDateString() === today.toDateString()) {
                timeString = `Today at ${lastUpdated.getHours()}:${String(lastUpdated.getMinutes()).padStart(2, '0')}`;
            } else {
                const options = { month: 'short', day: 'numeric' };
                timeString = `${lastUpdated.toLocaleDateString('en-US', options)} at ${lastUpdated.getHours()}:${String(lastUpdated.getMinutes()).padStart(2, '0')}`;
            }
            
            lastUpdatedEl.textContent = timeString;
        }
        
    } catch (error) {
        console.error('Error updating bottom bar stats:', error);
    }
} 