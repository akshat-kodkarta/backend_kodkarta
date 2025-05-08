# Users API Documentation

This documentation covers all API endpoints related to user authentication and management.

## Authentication

The API uses JWT (JSON Web Tokens) for authentication. Most endpoints require an `Authorization` header with a Bearer token:

```
Authorization: Bearer <access_token>
```

## Response Format

All API responses follow a consistent format:

### Success Response Format
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    // Response data here
  }
}
```

### Error Response Format
```json
{
  "status": "failed",
  "message": "Error description"
}
```

## API Endpoints

### 1. Health Check

Check if the API service is running.

**URL**: `/api/users/status/`  
**Method**: `GET`  
**Authentication**: None

**Response Body** (200 OK):
```json
{
  "status": "success",
  "message": "Service is running"
}
```

### 2. User Registration

Register a new user with email and password.

**URL**: `/api/users/register/`  
**Method**: `POST`  
**Authentication**: None

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "confirm_password": "securepassword123",
  "company_name": "My Company",
  "first_name": "John",
  "last_name": "Doe"
}
```

**Success Response** (201 Created):
```json
{
  "status": "success",
  "message": "User registered successfully",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "My Company"
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "status": "failed",
  "message": "A user with this email already exists.",
  "errors": {
    "email": ["A user with this email already exists."]
  }
}
```

### 3. User Login

Authenticate a user with email and password.

**URL**: `/api/users/login/`  
**Method**: `POST`  
**Authentication**: None

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "email": "user@example.com",
  "password": "securepassword123"
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "My Company"
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "status": "failed",
  "message": "Invalid email or password."
}
```

### 4. User Logout

Logout a user by blacklisting their refresh token.

**URL**: `/api/users/logout/`  
**Method**: `POST`  
**Authentication**: Required

**Request Headers**:
```
Content-Type: application/json
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "User logged out successfully"
}
```

**Error Response** (400 Bad Request):
```json
{
  "status": "failed",
  "message": "Refresh token is required"
}
```

### 5. Token Refresh

Get a new access token using a refresh token.

**URL**: `/api/users/refresh-token/`  
**Method**: `POST`  
**Authentication**: None

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Success Response** (200 OK):
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Error Response** (401 Unauthorized):
```json
{
  "status": "failed",
  "message": "Token is invalid or expired"
}
```

### 6. Google Login

Authenticate or register a user using a Google ID token.

**URL**: `/api/users/login/google/`  
**Method**: `POST`  
**Authentication**: None

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "token": "google_id_token_from_client"
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "Google login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "My Company"
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "status": "failed",
  "message": "Invalid Google token. Please try again."
}
```

### 7. GitHub Authorization URL

Get a GitHub authorization URL to start the OAuth flow.

**URL**: `/api/users/github/auth/`  
**Method**: `GET`  
**Authentication**: None

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "GitHub authorization URL generated",
  "data": {
    "url": "https://github.com/login/oauth/authorize?client_id=your_client_id&redirect_uri=your_redirect_uri&scope=user:email&state=random_state_string",
    "state": "random_state_string"
  }
}
```

**Error Response** (500 Internal Server Error):
```json
{
  "status": "failed",
  "message": "Failed to generate GitHub authorization URL."
}
```

### 8. GitHub Login

Authenticate or register a user using a GitHub authorization code.

**URL**: `/api/users/login/github/`  
**Method**: `POST`  
**Authentication**: None

**Request Headers**:
```
Content-Type: application/json
```

**Request Body**:
```json
{
  "code": "github_oauth_code_from_callback"
}
```

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "GitHub login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "company_name": "My Company"
    },
    "tokens": {
      "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
      "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
    }
  }
}
```

**Error Response** (400 Bad Request):
```json
{
  "status": "failed",
  "message": "Failed to obtain access token from GitHub. Please try again."
}
```

### 9. GitHub Callback Handler

Handle the GitHub OAuth callback with code in URL parameters.

**URL**: `/api/users/github/callback/`  
**Method**: `GET`  
**Authentication**: None

**Query Parameters**:
- `code`: The authorization code from GitHub
- `state`: The state parameter for CSRF protection

**Note**: This endpoint internally calls the GitHub Login endpoint and returns the same response format.

### 10. User Profile

Get the authenticated user's profile.

**URL**: `/api/users/profile/`  
**Method**: `GET`  
**Authentication**: Required

**Request Headers**:
```
Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...
```

**Request Body**: None

**Success Response** (200 OK):
```json
{
  "status": "success",
  "message": "Profile retrieved successfully",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "company_name": "My Company"
  }
}
```

**Error Response** (401 Unauthorized):
```json
{
  "status": "failed",
  "message": "Authentication credentials were not provided."
}
```

## Error Codes

Common HTTP status codes returned by the API:

- `200 OK`: Request succeeded
- `201 Created`: Resource successfully created
- `400 Bad Request`: Invalid input parameters
- `401 Unauthorized`: Authentication required or failed
- `403 Forbidden`: Permission denied
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error

## GitHub OAuth Flow

The GitHub OAuth authentication flow follows these steps:

1. **Frontend Initiates Auth Flow**:
   - Frontend calls `/api/users/github/auth/` to get an authorization URL
   - Frontend stores the returned `state` parameter in localStorage for CSRF protection
   - Frontend redirects the user to the returned GitHub authorization URL

2. **User Authenticates with GitHub**:
   - User logs in to GitHub and authorizes the application
   - GitHub redirects back to the frontend's callback URL with an authorization `code` and the same `state` parameter

3. **Frontend Handles Callback**:
   - Frontend verifies that the `state` parameter matches what was stored in localStorage
   - Frontend sends the `code` to `/api/users/login/github/`
   - Backend exchanges the code for a GitHub access token
   - Backend retrieves the user's information and email from GitHub
   - Backend creates or authenticates the user and returns JWT tokens

4. **Frontend Completes Authentication**:
   - Frontend stores the JWT tokens
   - Frontend redirects to the authenticated area

### Setting Up GitHub OAuth

1. Create a GitHub OAuth App at GitHub.com → Settings → Developer settings → OAuth Apps
2. Set the callback URL to match your frontend's GitHub callback route
3. Configure your backend with the following environment variables:
   - `GITHUB_CLIENT_ID`: Your GitHub OAuth App's client ID
   - `GITHUB_CLIENT_SECRET`: Your GitHub OAuth App's client secret
   - `GITHUB_REDIRECT_URI`: Your frontend's callback URL (e.g., http://localhost:3000/auth/github/callback)

## Implementation Notes

### Social Authentication Flow

1. **Google Authentication**:
   - The client obtains a Google ID token from Google Sign-In
   - The client sends this token to the `/api/users/login/google/` endpoint
   - The server verifies the token with Google and authenticates the user

2. **GitHub Authentication**:
   - The client gets an authorization URL from `/api/users/github/auth/`
   - The client redirects to GitHub's OAuth authorization page
   - GitHub redirects back to the client with an authorization code
   - The client sends this code to the `/api/users/login/github/` endpoint
   - The server exchanges the code for an access token and authenticates the user

### Security Considerations

- Always use HTTPS in production
- JWTs are validated on every request
- Access tokens expire after 60 minutes
- Refresh tokens can be used to obtain new access tokens
- Refresh tokens are blacklisted on logout to prevent reuse
- Passwords are securely hashed using Django's password hashing system
- GitHub OAuth flow includes state parameter validation for CSRF protection

'




@api @context @wrappers @auth.js 

make sure we have gopd and clean code with good seperation of concerns, i.e. api's defined at one place, cojmpnonents at othjerm view other model other and page othere. 