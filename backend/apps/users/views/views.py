from django.shortcuts import render
from django.contrib.auth import authenticate
from django.core.exceptions import ValidationError
from rest_framework import status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
import requests
import json
import logging
import os
from django.conf import settings
import urllib.parse

from ..models.models import User
from ..serializers import (
    UserRegistrationSerializer, 
    UserSerializer,
    GoogleAuthSerializer,
    GithubAuthSerializer
)

logger = logging.getLogger(__name__)

def get_tokens_for_user(user):
    try:
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    except Exception as e:
        logger.error(f"Error generating tokens for user {user.email}: {str(e)}")
        raise


class HealthCheckView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    def get(self, request):
        return Response({"status": "success", "message": "Service is running"}, status=status.HTTP_200_OK)


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        try:
            # Log the request body to diagnose validation issues
            logger.debug(f"UserRegistrationView received data: {request.data}")
            
            serializer = UserRegistrationSerializer(data=request.data)
            if serializer.is_valid():
                user = serializer.save()
                tokens = get_tokens_for_user(user)
                return Response({
                    "status": "success",
                    "message": "User registered successfully",
                    "data": {
                        'user': UserSerializer(user).data,
                        'tokens': tokens
                    }
                }, status=status.HTTP_201_CREATED)
            
            # Handle specific validation errors
            error_message = "Validation error"
            if 'email' in serializer.errors and 'unique' in str(serializer.errors['email']).lower():
                error_message = "A user with this email already exists."
            elif 'password' in serializer.errors:
                error_message = "Password must be at least 8 characters long and contain letters and numbers."
            elif 'confirm_password' in serializer.errors:
                error_message = "Passwords do not match."
            
            logger.error(f"UserRegistrationView serializer errors: {serializer.errors}")
            return Response({
                "status": "failed", 
                "message": error_message,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            logger.error(f"Registration error: {str(e)}")
            return Response({
                "status": "failed",
                "message": "An unexpected error occurred during registration."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class EmailLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        try:
            # Log the request body to diagnose validation issues
            logger.debug(f"EmailLoginView received data: {request.data}")
            
            email = request.data.get('email', '')
            password = request.data.get('password', '')
            
            if not email:
                logger.error("EmailLoginView error: Email is required")
                return Response({
                    "status": "failed",
                    "message": "Email is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not password:
                logger.error("EmailLoginView error: Password is required")
                return Response({
                    "status": "failed",
                    "message": "Password is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = authenticate(email=email, password=password)
            
            if not user:
                # For security reasons, we don't want to reveal whether an email exists or not
                return Response({
                    "status": "failed",
                    "message": "Invalid email or password."
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            if not user.is_active:
                return Response({
                    "status": "failed",
                    "message": "This account has been deactivated."
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            tokens = get_tokens_for_user(user)
            return Response({
                "status": "success",
                "message": "Login successful",
                "data": {
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return Response({
                "status": "failed",
                "message": "An unexpected error occurred during login."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        try:
            # Log the request body to diagnose validation issues
            logger.debug(f"GoogleLoginView received data: {request.data}")
            
            serializer = GoogleAuthSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"GoogleLoginView serializer errors: {serializer.errors}")
                return Response({
                    "status": "failed",
                    "message": "Invalid request. Token is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = serializer.validated_data['token']
            is_auth_code = serializer.validated_data.get('is_auth_code', False)
            
            if is_auth_code:
                # Handle authorization code flow
                try:
                    logger.debug(f"GoogleLoginView processing authorization code")
                    
                    # Log the entire request data to see what's being received
                    logger.debug(f"GoogleLoginView request data: {request.data}")
                    
                    # Exchange authorization code for tokens
                    client_id = os.environ.get('NEXT_PUBLIC_GOOGLE_CLIENT_ID')
                    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET')
                    
                    # First try to get redirect_uri from request data (sent by frontend)
                    # Fall back to environment variable if not in request
                    redirect_uri = request.data.get('redirect_uri') or os.environ.get('NEXT_PUBLIC_GOOGLE_REDIRECT_URI')
                    
                    if not client_id or not client_secret:
                        logger.error(f"Google client credentials missing. Client ID: {'Set' if client_id else 'Missing'}, Client Secret: {'Set' if client_secret else 'Missing'}")
                        return Response({
                            "status": "failed",
                            "message": "Google authentication is not properly configured on the server."
                        }, status=status.HTTP_501_NOT_IMPLEMENTED)
                    
                    if not redirect_uri:
                        logger.error("GoogleLoginView: Redirect URI is missing from both request and environment variables")
                        return Response({
                            "status": "failed",
                            "message": "Google redirect URI is missing. Please check your configuration."
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    logger.debug(f"GoogleLoginView using redirect_uri: {redirect_uri}")
                    
                    token_url = 'https://oauth2.googleapis.com/token'
                    payload = {
                        'code': token,
                        'client_id': client_id,
                        'client_secret': client_secret,
                        'redirect_uri': redirect_uri,
                        'grant_type': 'authorization_code'
                    }
                    
                    logger.debug(f"GoogleLoginView token exchange payload: {payload}")
                    
                    response = requests.post(token_url, data=payload)
                    
                    if response.status_code != 200:
                        logger.error(f"GoogleLoginView code exchange failed: {response.text}")
                        return Response({
                            "status": "failed",
                            "message": "Failed to exchange authorization code. Please try again."
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    token_data = response.json()
                    id_token = token_data.get('id_token')
                    
                    if not id_token:
                        logger.error("GoogleLoginView: No ID token received from code exchange")
                        return Response({
                            "status": "failed",
                            "message": "Failed to authenticate with Google. No ID token received."
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Now verify the ID token
                    response = requests.get(
                        f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={id_token}'
                    )
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Google API error during code exchange: {str(e)}")
                    return Response({
                        "status": "failed",
                        "message": "Could not connect to Google authentication service. Please try again later."
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            else:
                # Original ID token flow
                try:
                    logger.debug(f"GoogleLoginView verifying ID token with Google API: {token[:10]}...")
                    response = requests.get(
                        f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}'
                    )
                except requests.exceptions.RequestException as e:
                    logger.error(f"Google API error: {str(e)}")
                    return Response({
                        "status": "failed",
                        "message": "Could not connect to Google authentication service. Please try again later."
                    }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            logger.debug(f"GoogleLoginView Google API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"GoogleLoginView token validation failed: {response.text}")
                return Response({
                    "status": "failed",
                    "message": "Invalid Google token. Please try again."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            google_data = response.json()
            logger.debug(f"GoogleLoginView successful Google API response: {google_data}")
            
            email = google_data.get('email')
            
            if not email:
                logger.error("GoogleLoginView: Email not found in Google data")
                return Response({
                    "status": "failed",
                    "message": "Email not found in Google data. Please ensure your Google account has an email."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # For authorization code flow, we verify against the original client_id
            if is_auth_code:
                expected_client_id = os.environ.get('NEXT_PUBLIC_GOOGLE_CLIENT_ID')
            else:
                expected_client_id = os.environ.get('NEXT_PUBLIC_GOOGLE_CLIENT_ID')
                
            if google_data.get('aud') != expected_client_id:
                logger.error(f"Token validation failed: audience mismatch - expected {expected_client_id}, got {google_data.get('aud')}")
                return Response({
                    "status": "failed", 
                    "message": "Invalid client ID"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if user exists
            try:
                user = User.objects.get(email=email)
                
                logger.debug(f"GoogleLoginView: Found existing user with email {email}, auth_provider={user.auth_provider}, auth_id={'Set' if user.auth_id else 'None'}")
                
                # Always update to Google auth if not already
                if not user.auth_provider or user.auth_provider not in ['google']:
                    logger.info(f"GoogleLoginView: Updating user {email} auth provider to Google from {user.auth_provider}")
                    user.auth_provider = 'google'
                    user.auth_id = google_data.get('sub')
                    user.save()
                # Update auth_id if it doesn't match or is missing
                elif user.auth_provider == 'google' and (not user.auth_id or user.auth_id != google_data.get('sub')):
                    logger.info(f"GoogleLoginView: Updating Google auth_id for user {email}")
                    user.auth_id = google_data.get('sub')
                    user.save()
                
                if not user.is_active:
                    logger.warning(f"GoogleLoginView: Deactivated account attempt for {email}")
                    return Response({
                        "status": "failed",
                        "message": "This account has been deactivated."
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                logger.info(f"GoogleLoginView: User {email} authentication successful")
                
            except User.DoesNotExist:
                # Create new user
                try:
                    logger.info(f"GoogleLoginView: Creating new user with email {email}")
                    user = User.objects.create_user(
                        email=email,
                        auth_id=google_data.get('sub'),
                        auth_provider='google',
                        first_name=google_data.get('given_name', ''),
                        last_name=google_data.get('family_name', ''),
                        password=None  # No password for social auth
                    )
                except Exception as e:
                    logger.error(f"Error creating user from Google auth: {str(e)}")
                    return Response({
                        "status": "failed",
                        "message": "Failed to create user account."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            tokens = get_tokens_for_user(user)
            logger.info(f"GoogleLoginView: Successful login for {email}")
            return Response({
                "status": "success",
                "message": "Google login successful",
                "data": {
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }
            })
        
        except Exception as e:
            logger.error(f"Google login error: {str(e)}")
            return Response({
                "status": "failed",
                "message": "An unexpected error occurred during Google login."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GitHubAuthorizationView(APIView):
    """
    View to generate the GitHub authorization URL
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def get(self, request):
        try:
            # Get GitHub OAuth settings
            client_id = os.environ.get('GITHUB_CLIENT_ID')
            redirect_uri = os.environ.get('GITHUB_REDIRECT_URI')
            scopes = getattr(settings, 'GITHUB_SCOPES', ['user:email'])
            
            logger.debug(f"GitHubAuthorizationView: Using client_id: {'Set' if client_id else 'Missing'}, redirect_uri: {redirect_uri}")
            
            if not client_id:
                logger.error("GitHubAuthorizationView: Missing GITHUB_CLIENT_ID environment variable")
                return Response({
                    "status": "failed",
                    "message": "GitHub authentication is not properly configured on the server."
                }, status=status.HTTP_501_NOT_IMPLEMENTED)
            
            # Generate state parameter to prevent CSRF
            state = os.urandom(16).hex()
            
            # Build the authorization URL
            auth_url = 'https://github.com/login/oauth/authorize'
            params = {
                'client_id': client_id,
                'redirect_uri': redirect_uri,
                'scope': ' '.join(scopes),
                'state': state,
            }
            
            url = f"{auth_url}?{urllib.parse.urlencode(params)}"
            
            logger.debug(f"GitHubAuthorizationView: Generated URL: {url}")
            
            return Response({
                "status": "success",
                "message": "GitHub authorization URL generated",
                "data": {
                    "url": url,
                    "state": state
                }
            })
            
        except Exception as e:
            logger.error(f"Error generating GitHub auth URL: {str(e)}")
            return Response({
                "status": "failed",
                "message": "Failed to generate GitHub authorization URL."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GithubLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        try:
            # Log the request body to diagnose validation issues
            logger.debug(f"GithubLoginView received data: {request.data}")
            
            serializer = GithubAuthSerializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"GithubLoginView serializer errors: {serializer.errors}")
                return Response({
                    "status": "failed",
                    "message": "Invalid request. Authorization code is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            code = serializer.validated_data['code']
            
            # Get GitHub OAuth credentials from environment variables
            client_id = os.environ.get('GITHUB_CLIENT_ID')
            client_secret = os.environ.get('GITHUB_CLIENT_SECRET')
            redirect_uri = os.environ.get('GITHUB_REDIRECT_URI')
            
            # Log the GitHub OAuth configuration 
            logger.debug(f"GithubLoginView OAuth config: client_id={'Set' if client_id else 'Missing'}, client_secret={'Set' if client_secret else 'Missing'}, redirect_uri={redirect_uri}")
            
            if not client_id or not client_secret:
                logger.error(f"GitHub authentication misconfigured. Client ID: {'Set' if client_id else 'Missing'}, Client Secret: {'Set' if client_secret else 'Missing'}")
                return Response({
                    "status": "failed",
                    "message": "GitHub authentication is not properly configured on the server."
                }, status=status.HTTP_501_NOT_IMPLEMENTED)
                
            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
                'redirect_uri': redirect_uri
            }
            
            logger.debug(f"GitHub token exchange payload: {data}")
            
            try:
                # Exchange the code for an access token
                logger.info(f"GithubLoginView: Exchanging authorization code for access token")
                response = requests.post(
                    'https://github.com/login/oauth/access_token',
                    data=data,
                    headers={'Accept': 'application/json'}
                )
                
                if response.status_code != 200:
                    logger.error(f"GitHub token error: {response.text}")
                    return Response({
                        "status": "failed",
                        "message": "Failed to obtain access token from GitHub. Please try again."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                token_data = response.json()
                
                if 'error' in token_data:
                    error_msg = token_data.get('error_description', token_data['error'])
                    logger.error(f"GitHub OAuth error: {error_msg}")
                    return Response({
                        "status": "failed",
                        "message": f"GitHub error: {error_msg}"
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                access_token = token_data.get('access_token')
                if not access_token:
                    return Response({
                        "status": "failed",
                        "message": "No access token received from GitHub."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Get user info from GitHub API
                response = requests.get(
                    'https://api.github.com/user',
                    headers={
                        'Authorization': f'token {access_token}',
                        'Accept': 'application/json'
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"GitHub API error: {response.text}")
                    return Response({
                        "status": "failed",
                        "message": "Failed to get user info from GitHub. Please try again."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                github_data = response.json()
                logger.info(f"GitHub user data: {github_data}")
                
                # Get user's email (GitHub may not provide email in user data)
                email_response = requests.get(
                    'https://api.github.com/user/emails',
                    headers={
                        'Authorization': f'token {access_token}',
                        'Accept': 'application/json'
                    }
                )
                
                if email_response.status_code != 200:
                    logger.error(f"GitHub email API error: {email_response.text}")
                    return Response({
                        "status": "failed",
                        "message": "Failed to get email from GitHub. Please ensure your GitHub account has a verified email."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                emails = email_response.json()
                logger.info(f"GitHub emails: {emails}")
                
                if not emails or len(emails) == 0:
                    return Response({
                        "status": "failed",
                        "message": "No emails found in your GitHub account. Please add a verified email to your GitHub account."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                primary_email = next((e['email'] for e in emails if e['primary']), None)
                if not primary_email:
                    # If no primary email, take the first verified email
                    primary_email = next((e['email'] for e in emails if e['verified']), None)
                
                if not primary_email:
                    return Response({
                        "status": "failed",
                        "message": "No verified email found in your GitHub account. Please verify your email in GitHub."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"GitHub API error: {str(e)}")
                return Response({
                    "status": "failed",
                    "message": "Could not connect to GitHub. Please try again later."
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Check if user exists
            try:
                user = User.objects.get(email=primary_email)
                
                logger.debug(f"GithubLoginView: Found existing user with email {primary_email}, auth_provider={user.auth_provider}, auth_id={'Set' if user.auth_id else 'None'}")
                
                # Always update to GitHub auth if not already
                if not user.auth_provider or user.auth_provider not in ['github']:
                    logger.info(f"GithubLoginView: Updating user {primary_email} auth provider to GitHub from {user.auth_provider}")
                    user.auth_provider = 'github'
                    user.auth_id = str(github_data.get('id'))
                    user.save()
                # Update auth_id if it doesn't match or is missing
                elif user.auth_provider == 'github' and (not user.auth_id or user.auth_id != str(github_data.get('id'))):
                    logger.info(f"GithubLoginView: Updating GitHub auth_id for user {primary_email}")
                    user.auth_id = str(github_data.get('id'))
                    user.save()
                
                if not user.is_active:
                    logger.warning(f"GithubLoginView: Deactivated account attempt for {primary_email}")
                    return Response({
                        "status": "failed",
                        "message": "This account has been deactivated."
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
                logger.info(f"GithubLoginView: User {primary_email} authentication successful")
                
            except User.DoesNotExist:
                # Create new user
                try:
                    name_parts = github_data.get('name', '').split(' ', 1)
                    first_name = name_parts[0] if name_parts else ''
                    last_name = name_parts[1] if len(name_parts) > 1 else ''
                    
                    user = User.objects.create_user(
                        email=primary_email,
                        auth_id=str(github_data.get('id')),
                        auth_provider='github',
                        first_name=first_name,
                        last_name=last_name,
                        password=None  # No password for social auth
                    )
                except Exception as e:
                    logger.error(f"Error creating user from GitHub auth: {str(e)}")
                    return Response({
                        "status": "failed",
                        "message": "Failed to create user account."
                    }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            tokens = get_tokens_for_user(user)
            return Response({
                "status": "success",
                "message": "GitHub login successful",
                "data": {
                    'user': UserSerializer(user).data,
                    'tokens': tokens
                }
            })
        
        except Exception as e:
            logger.error(f"GitHub login error: {str(e)}")
            return Response({
                "status": "failed",
                "message": "An unexpected error occurred during GitHub login."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def get(self, request):
        try:
            serializer = UserSerializer(request.user)
            return Response({
                "status": "success",
                "message": "Profile retrieved successfully",
                "data": serializer.data
            })
        except Exception as e:
            logger.error(f"Profile error for user {request.user.id}: {str(e)}")
            return Response({
                "status": "failed",
                "message": "Failed to retrieve user profile."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    authentication_classes = [JWTAuthentication]
    
    def post(self, request):
        try:
            # Get the refresh token from request
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({
                    "status": "failed",
                    "message": "Refresh token is required"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Blacklist the refresh token
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
                return Response({
                    "status": "success",
                    "message": "User logged out successfully"
                }, status=status.HTTP_200_OK)
            except TokenError:
                return Response({
                    "status": "failed",
                    "message": "Invalid or expired token"
                }, status=status.HTTP_400_BAD_REQUEST)
            
        except Exception as e:
            logger.error(f"Logout error for user {request.user.id}: {str(e)}")
            return Response({
                "status": "failed",
                "message": "An error occurred during logout"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GitHubOAuthCallbackView(APIView):
    """
    A dedicated view to handle GitHub OAuth redirect
    This is useful for frontend integration to simplify the flow
    """
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def get(self, request):
        # Extract the code from the query parameters
        code = request.GET.get('code')
        
        if not code:
            return Response({
                "status": "failed",
                "message": "No authorization code provided"
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create a mock request for the GithubLoginView
        mock_request = type('MockRequest', (), {'data': {'code': code}})()
        
        # Forward to the existing GitHub login view
        github_view = GithubLoginView()
        return github_view.post(mock_request)
