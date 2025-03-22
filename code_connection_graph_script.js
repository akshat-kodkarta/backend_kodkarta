document.addEventListener('DOMContentLoaded', function() {
    const GITHUB_API_BASE = 'https://api.github.com';
    const GITHUB_TOKEN = localStorage.getItem('GITHUB_TOKEN') || prompt('Enter GitHub Personal Access Token:');

    // State management
    const state = {
        currentView: 'organizations',
        organizations: [],
        repositories: [],
        contributors: [],
        files: []
    };

    // Fetch GitHub Organizations
    async function fetchGitHubOrganizations() {
        try {
            const response = await fetch(`${GITHUB_API_BASE}/user/orgs`, {
                headers: {
                    'Authorization': `token ${GITHUB_TOKEN}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });

            if (!response.ok) {
                // More detailed error logging
                const errorBody = await response.text();
                console.error(`GitHub API Error: ${response.status}`, errorBody);
                throw new Error(`Failed to fetch organizations: ${response.statusText}`);
            }

            const organizations = await response.json();
            return organizations.map((org, index) => ({
                id: index + 1,
                name: org.login,
                type: 'organization',
                group: 'organization',
                size: 20,
                avatar: org.avatar_url,
                description: org.description || 'No description'
            }));
        } catch (error) {
            console.error('Comprehensive Error in fetchGitHubOrganizations:', error);
            // Fallback mechanism
            return [
                {
                    id: 1,
                    name: 'Error Fetching Organizations',
                    type: 'organization',
                    group: 'error',
                    size: 20
                }
            ];
        }
    }

    // Fetch Repositories for an Organization
    async function fetchOrganizationRepositories(orgName) {
        try {
            const response = await fetch(`${GITHUB_API_BASE}/orgs/${orgName}/repos`, {
                headers: {
                    'Authorization': `token ${GITHUB_TOKEN}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch repositories for ${orgName}`);
            }

            const repositories = await response.json();
            return repositories.map((repo, index) => ({
                id: index + 1000,  // Offset to avoid ID conflicts
                name: repo.name,
                type: 'repository',
                group: 'repository',
                size: 15,
                full_name: repo.full_name,
                description: repo.description || 'No description'
            }));
        } catch (error) {
            console.error(`Error fetching repositories for ${orgName}:`, error);
            return [];
        }
    }

    // Fetch Repository Contributors
    async function fetchRepositoryContributors(repoFullName) {
        try {
            const response = await fetch(`${GITHUB_API_BASE}/repos/${repoFullName}/contributors`, {
                headers: {
                    'Authorization': `token ${GITHUB_TOKEN}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch contributors for ${repoFullName}`);
            }

            const contributors = await response.json();
            return contributors.map((contributor, index) => ({
                id: index + 2000,  // Offset to avoid ID conflicts
                name: contributor.login,
                type: 'contributor',
                group: 'contributor',
                size: 10,
                contributions: contributor.contributions
            }));
        } catch (error) {
            console.error(`Error fetching contributors for ${repoFullName}:`, error);
            return [];
        }
    }

    // Fetch Repository Files
    async function fetchRepositoryFiles(repoFullName) {
        try {
            const response = await fetch(`${GITHUB_API_BASE}/repos/${repoFullName}/contents`, {
                headers: {
                    'Authorization': `token ${GITHUB_TOKEN}`,
                    'Accept': 'application/vnd.github.v3+json'
                }
            });

            if (!response.ok) {
                throw new Error(`Failed to fetch files for ${repoFullName}`);
            }

            const files = await response.json();
            return files.map((file, index) => ({
                id: index + 3000,  // Offset to avoid ID conflicts
                name: file.name,
                type: file.type,
                group: file.type,
                size: 5,
                path: file.path
            }));
        } catch (error) {
            console.error(`Error fetching files for ${repoFullName}:`, error);
            return [];
        }
    }

    // Create Graph Visualization
    function createGraph(nodes, links) {
        // Clear previous graph
        d3.select("#container svg").remove();

        const container = document.getElementById('container');
        const width = container.clientWidth;
        const height = container.clientHeight;

        const svg = d3.select("#container")
            .append("svg")
            .attr("width", "100%")
            .attr("height", "100%")
            .attr("viewBox", `0 0 ${width} ${height}`);

        const colorScale = d3.scaleOrdinal()
            .domain(['root', 'organization', 'repository', 'contributor', 'file'])
            .range(["#3366cc", "#109618", "#ff9900", "#dc3912", "#4285f4"]);

        const simulation = d3.forceSimulation(nodes)
            .force("link", d3.forceLink(links).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-200))
            .force("center", d3.forceCenter(width / 2, height / 2))
            .force("collide", d3.forceCollide(20));

        // Create links
        const link = svg.append("g")
            .selectAll("line")
            .data(links)
            .enter().append("line")
            .attr("stroke", d => colorScale(d.type))
            .attr("stroke-opacity", 0.6)
            .attr("stroke-width", 2);

        // Create nodes
        const node = svg.append("g")
            .selectAll("circle")
            .data(nodes)
            .enter().append("circle")
            .attr("r", d => d.size || 10)
            .attr("fill", d => colorScale(d.group))
            .attr("stroke", "#fff")
            .attr("stroke-width", 1.5)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        // Add labels
        const labels = svg.append("g")
            .selectAll("text")
            .data(nodes)
            .enter().append("text")
            .text(d => d.name)
            .attr("font-size", 10)
            .attr("dx", 12)
            .attr("dy", ".35em");

        // Tooltip
        const tooltip = d3.select("#tooltip");
        node.on("mouseover", (event, d) => {
            tooltip.transition()
                .duration(200)
                .style("opacity", .9);
            tooltip.html(`
                <strong>${d.name}</strong><br>
                Path: ${d.path}<br>
                Type: ${d.type}<br>
                Group: ${d.group}
            `)
            .style("left", (event.pageX + 10) + "px")
            .style("top", (event.pageY - 28) + "px");
        })
        .on("mouseout", () => {
            tooltip.transition()
                .duration(500)
                .style("opacity", 0);
        });

        // Update stats
        document.getElementById('totalFiles').querySelector('span').textContent = nodes.length;
        document.getElementById('totalConnections').querySelector('span').textContent = links.length;
        
        // Count connection types
        const connectionTypeCounts = links.reduce((acc, link) => {
            acc[link.type] = (acc[link.type] || 0) + 1;
            return acc;
        }, {});

        document.getElementById('dependencyCount').textContent = `Dependencies: ${connectionTypeCounts['organization'] || 0}`;
        document.getElementById('importCount').textContent = `Imports: ${connectionTypeCounts['repository'] || 0}`;
        document.getElementById('functionCallCount').textContent = `Function Calls: ${connectionTypeCounts['contributor'] || 0}`;

        // Simulation tick
        simulation.on("tick", () => {
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);
            
            node
                .attr("cx", d => d.x)
                .attr("cy", d => d.y);
            
            labels
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

        // Filter functionality
        document.getElementById('connectionTypeFilter').addEventListener('change', function() {
            const filterValue = this.value;
            
            if (filterValue === 'all') {
                node.style('opacity', 1);
                link.style('opacity', 0.6);
            } else {
                node.style('opacity', d => 
                    d.group === filterValue || d.type === 'root' ? 1 : 0.1
                );
                link.style('opacity', d => 
                    d.type === filterValue ? 0.6 : 0.1
                );
            }
        });
    }

    // Main Initialization Function
    async function initializeGraph() {
        try {
            console.log('Initializing Graph...'); // Debug log

            // Validate token
            if (!GITHUB_TOKEN) {
                console.error('No GitHub Token Available');
                // Show user-friendly error
                document.getElementById('repoName').textContent = 'GitHub Token Missing';
                return;
            }

            // Get initial graph data
            const { nodes: initialNodes, links: initialLinks } = getInitialGraphData();
            console.log('Initial Nodes:', initialNodes);

            // Fetch organizations with comprehensive logging
            const organizations = await fetchGitHubOrganizations();
            console.log('Fetched Organizations:', organizations);

            if (organizations.length === 0) {
                console.warn('No organizations found');
                // Update UI to reflect no organizations
                document.getElementById('repoName').textContent = 'No Organizations Found';
                return;
            }

            // Create complete graph with organizations
            const completeNodes = [
                ...initialNodes,
                ...organizations
            ];

            const completeLinks = organizations.map((org, index) => ({
                source: 0,
                target: org.id,
                value: 1
            }));

            console.log('Complete Nodes:', completeNodes);
            console.log('Complete Links:', completeLinks);

            // Render initial graph
            createAssetGraph(completeNodes, completeLinks);

            // Update stats
            document.getElementById('repoName').textContent = 'GitHub Organizations';
            document.getElementById('totalAssets').textContent = `Total Organizations: ${organizations.length}`;
            document.getElementById('iacFiles').textContent = 'Explore Organizations';
            document.getElementById('dependencyFiles').textContent = 'Click to Dive Deeper';

        } catch (error) {
            console.error('Comprehensive Initialization Error:', error);
            // User-friendly error handling
            document.getElementById('repoName').textContent = 'Graph Initialization Failed';
        }
    }

    // Start the graph initialization
    initializeGraph();
}); 