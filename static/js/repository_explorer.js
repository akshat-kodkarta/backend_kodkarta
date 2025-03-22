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
            // Successful response handling
            if (data.status === 'success') {
                resultOutput.innerHTML = `
                    <h4>Repository: ${data.repository}</h4>
                    <p>Processing Time: ${data.processing_time.toFixed(2)} seconds</p>
                    <h5>Contents Summary:</h5>
                    <pre>${JSON.stringify(data.contents, null, 2)}</pre>
                `;
                
                // Create Asset Connection Map
                createAssetConnectionMap(data);
            } else {
                throw new Error(data.error || 'Unknown error occurred');
            }
        })
        .catch(error => {
            // Error handling
            resultOutput.innerHTML = `
                <div class="alert alert-danger">
                    <strong>Error:</strong> ${error.message}
                </div>
            `;
            console.error('Exploration Error:', error);
        });
    }
});
