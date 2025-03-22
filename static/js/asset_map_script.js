// GitHub API base URL
const GITHUB_API_BASE = 'https://api.github.com';

// State management
const state = {
    currentView: 'organizations',
    organizations: [],
    repositories: [],
    selectedOrg: null
};

// Function to safely get initial graph data
function getInitialGraphData() {
    const defaultNodes = [
        {id: 0, name: 'GitHub Organizations', type: 'root', group: 'root', size: 30}
    ];
    const defaultLinks = [];

    return { nodes: defaultNodes, links: defaultLinks };
}

// Fetch GitHub Organizations
async function fetchGitHubOrganizations() {
    try {
        // You might want to replace this with a more secure authentication method
        const response = await fetch(`${GITHUB_API_BASE}/user/orgs`, {
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`, // Securely manage this token
                'Accept': 'application/vnd.github.v3+json'
            }
        });

        if (!response.ok) {
            throw new Error('Failed to fetch organizations');
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
        console.error('Error fetching organizations:', error);
        return [];
    }
}

// Fetch Repositories for a specific Organization
async function fetchOrganizationRepositories(orgName) {
    try {
        const response = await fetch(`${GITHUB_API_BASE}/orgs/${orgName}/repos`, {
            headers: {
                'Authorization': `token ${GITHUB_TOKEN}`, // Securely manage this token
                'Accept': 'application/vnd.github.v3+json'
            }
        });

        if (!response.ok) {
            throw new Error(`Failed to fetch repositories for ${orgName}`);
        }

        const repositories = await response.json();
        return repositories.map((repo, index) => ({
            id: index + 1000, // Offset to avoid ID conflicts
            name: repo.name,
            type: 'repository',
            group: 'repository',
            size: 15,
            description: repo.description || 'No description',
            language: repo.language,
            stars: repo.stargazers_count,
            url: repo.html_url
        }));
    } catch (error) {
        console.error(`Error fetching repositories for ${orgName}:`, error);
        return [];
    }
}

// Create D3.js Visualization
function createAssetGraph(nodes, links) {
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

    // Color scale
    const colorScale = d3.scaleOrdinal()
        .domain(['root', 'organization', 'repository'])
        .range(["#3366cc", "#109618", "#ff9900"]);

    // Force simulation
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
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", 2);

    // Create nodes
    const node = svg.append("g")
        .selectAll("circle")
        .data(nodes)
        .enter().append("circle")
        .attr("r", d => d.size)
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

    // Node click handler
    node.on("click", async (event, d) => {
        if (d.type === 'organization') {
            state.selectedOrg = d.name;
            const repositories = await fetchOrganizationRepositories(d.name);
            updateGraphWithRepositories(repositories, d);
        }
    });

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
}

// Update graph with repositories
async function updateGraphWithRepositories(repositories, orgNode) {
    const rootNode = { id: 0, name: 'GitHub Organizations', type: 'root', group: 'root', size: 30 };
    
    const nodes = [
        rootNode,
        orgNode,
        ...repositories
    ];

    const links = [
        { source: 0, target: orgNode.id, value: 2 },
        ...repositories.map((repo, index) => ({
            source: orgNode.id,
            target: repo.id,
            value: 1
        }))
    ];

    createAssetGraph(nodes, links);

    // Update stats
    document.getElementById('repoName').textContent = `Organization: ${orgNode.name}`;
    document.getElementById('totalAssets').textContent = `Total Repositories: ${repositories.length}`;
    document.getElementById('iacFiles').textContent = `Repositories with IaC: ${repositories.filter(r => r.language === 'HCL').length}`;
    document.getElementById('dependencyFiles').textContent = `Repositories with Dependencies: ${repositories.filter(r => r.language !== null).length}`;
}

// Main initialization function
async function initializeGraph() {
    try {
        // Get initial graph data
        const { nodes: initialNodes, links: initialLinks } = getInitialGraphData();

        // Fetch organizations
        const organizations = await fetchGitHubOrganizations();

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

        // Render initial graph
        createAssetGraph(completeNodes, completeLinks);

        // Update stats
        document.getElementById('repoName').textContent = 'GitHub Organizations';
        document.getElementById('totalAssets').textContent = `Total Organizations: ${organizations.length}`;
        document.getElementById('iacFiles').textContent = 'Explore Organizations';
        document.getElementById('dependencyFiles').textContent = 'Click to Dive Deeper';

    } catch (error) {
        console.error('Initialization error:', error);
    }
}

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', initializeGraph);

// Asset Connection Map Visualization
function createAssetConnectionMap(repositoryData) {
    // Clear previous visualization
    d3.select("#asset-map-container").selectAll("*").remove();

    // Prepare data for visualization
    const nodes = [];
    const links = [];

    // Root node
    nodes.push({
        id: 0,
        name: repositoryData.repository,
        type: 'root',
        group: 'repository'
    });

    // Process repository contents
    repositoryData.contents.forEach((item, index) => {
        // Create node for each asset
        nodes.push({
            id: index + 1,
            name: item.name,
            type: item.type,
            path: item.path,
            group: getAssetGroup(item)
        });

        // Create link from root to asset
        links.push({
            source: 0,
            target: index + 1,
            value: 1
        });
    });

    // D3.js Force-Directed Graph
    const width = 800;
    const height = 600;

    const svg = d3.select("#asset-map-container")
        .append("svg")
        .attr("width", width)
        .attr("height", height);

    const simulation = d3.forceSimulation(nodes)
        .force("link", d3.forceLink(links).id(d => d.id))
        .force("charge", d3.forceManyBody().strength(-200))
        .force("center", d3.forceCenter(width / 2, height / 2));

    // Create links
    const link = svg.append("g")
        .selectAll("line")
        .data(links)
        .enter()
        .append("line")
        .attr("stroke", "#999")
        .attr("stroke-opacity", 0.6)
        .attr("stroke-width", d => Math.sqrt(d.value));

    // Create nodes
    const node = svg.append("g")
        .selectAll("circle")
        .data(nodes)
        .enter()
        .append("circle")
        .attr("r", d => getNodeSize(d))
        .attr("fill", d => getNodeColor(d))
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));

    // Node labels
    const label = svg.append("g")
        .selectAll("text")
        .data(nodes)
        .enter()
        .append("text")
        .text(d => d.name)
        .attr("font-size", 10)
        .attr("dx", 12)
        .attr("dy", 4);

    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);

        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);

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
}

// Helper functions for node styling
function getAssetGroup(item) {
    const fileExtension = item.name.split('.').pop().toLowerCase();
    const assetGroups = {
        'py': 'python',
        'js': 'javascript',
        'json': 'config',
        'yaml': 'config',
        'md': 'documentation',
        'txt': 'text'
    };
    return assetGroups[fileExtension] || 'other';
}

function getNodeSize(node) {
    const sizeMap = {
        'root': 20,
        'python': 12,
        'javascript': 10,
        'config': 8,
        'documentation': 6,
        'text': 6
    };
    return sizeMap[node.group] || 5;
}

function getNodeColor(node) {
    const colorMap = {
        'root': '#007bff',
        'python': '#4B8BBE',
        'javascript': '#F0DB4F',
        'config': '#6A5ACD',
        'documentation': '#28a745',
        'text': '#6c757d'
    };
    return colorMap[node.group] || '#343a40';
} 