# backend_kodkarta
What's Happening
--- Scanning GitHub Repository: https://github.com/facebook/react ---
Request GET /repos/facebook/react failed with 403: rate limit exceeded
Setting next backoff to 3155.511063s

Rate Limit Exceeded (403): GitHub limits how many API requests you can make in a certain time period. For unauthenticated requests, this is typically 60 requests per hour.
2. Backoff Time: The code is implementing a backoff strategy, waiting approximately 52 minutes (3155 seconds) before trying again. This is the time until GitHub resets your rate limit.

Why This Happens
GitHub's API rate limits are:
Unauthenticated requests: 60 requests per hour (tracked by IP address)
Authenticated requests: 5,000 requests per hour (with a personal access token)
The React repository is large with thousands of files, and each file requires at least one API request to fetch its content. You're quickly hitting the limit.



Do it async based on the heirarchy level of the repository.

1. Scan the organization and the repositories.
2. When clicking on a repository, scan the repository and the files asynchronously.
    A. scan the files, the code, the dependencies, and the secrets.
3. Scan the repository and the files asynchronously in the background for the next level of heirarchy.
    A. scan the dependency and the code in the background for the next level of heirarchy.
    B. scan the category and the code in the background for the next level of heirarchy.
    C. scan the repository and the files in the background for the next level of heirarchy.
    D. scan the file and the code in the background for the next level of heirarchy.
    E. scan the secret and the code in the background for the next level of heirarchy.

Make sure we do this based on the number of Github API requests we have for that hour.
