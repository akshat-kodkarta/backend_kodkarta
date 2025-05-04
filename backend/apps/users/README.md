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

### 7. GitHub Login

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
  "code": "github_oauth_code_from_client"
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

### 8. User Profile

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

## Implementation Notes

### Social Authentication Flow

1. **Google Authentication**:
   - The client obtains a Google ID token from Google Sign-In
   - The client sends this token to the `/api/users/login/google/` endpoint
   - The server verifies the token with Google and authenticates the user

2. **GitHub Authentication**:
   - The client redirects to GitHub OAuth authorization page
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

'




@api @context @wrappers @auth.js 

make sure we have gopd and clean code with good seperation of concerns, i.e. api's defined at one place, cojmpnonents at othjerm view other model other and page othere. 