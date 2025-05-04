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
            email = request.data.get('email', '')
            password = request.data.get('password', '')
            
            if not email:
                return Response({
                    "status": "failed",
                    "message": "Email is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not password:
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
            serializer = GoogleAuthSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": "failed",
                    "message": "Invalid request. Token is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            token = serializer.validated_data['token']
            
            # Verify the Google token with Google's API
            try:
                response = requests.get(
                    f'https://www.googleapis.com/oauth2/v3/tokeninfo?id_token={token}'
                )
                
                if response.status_code != 200:
                    return Response({
                        "status": "failed",
                        "message": "Invalid Google token. Please try again."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                google_data = response.json()
                email = google_data.get('email')
                
                if not email:
                    return Response({
                        "status": "failed",
                        "message": "Email not found in Google data. Please ensure your Google account has an email."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Google API error: {str(e)}")
                return Response({
                    "status": "failed",
                    "message": "Could not connect to Google authentication service. Please try again later."
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            # Check if user exists
            try:
                user = User.objects.get(email=email)
                # Update Google ID if not set
                if not user.auth_provider == 'google':
                    return Response({
                        "status": "failed",
                        "message": f"This email is already registered with {user.auth_provider}. Please use that login method."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                if not user.auth_id:
                    user.auth_id = google_data.get('sub')
                    user.save()
                
                if not user.is_active:
                    return Response({
                        "status": "failed",
                        "message": "This account has been deactivated."
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
            except User.DoesNotExist:
                # Create new user
                try:
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


class GithubLoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        try:
            serializer = GithubAuthSerializer(data=request.data)
            if not serializer.is_valid():
                return Response({
                    "status": "failed",
                    "message": "Invalid request. Authorization code is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            code = serializer.validated_data['code']
            
            # Exchange code for token
            # You'll need to register your app with GitHub and get client_id and client_secret
            client_id = 'YOUR_GITHUB_CLIENT_ID'
            client_secret = 'YOUR_GITHUB_CLIENT_SECRET'
            
            if not client_id or not client_secret or client_id == 'YOUR_GITHUB_CLIENT_ID':
                return Response({
                    "status": "failed",
                    "message": "GitHub authentication is not properly configured on the server."
                }, status=status.HTTP_501_NOT_IMPLEMENTED)
                
            data = {
                'client_id': client_id,
                'client_secret': client_secret,
                'code': code,
            }
            
            try:
                response = requests.post(
                    'https://github.com/login/oauth/access_token',
                    data=data,
                    headers={'Accept': 'application/json'}
                )
                
                if response.status_code != 200:
                    return Response({
                        "status": "failed",
                        "message": "Failed to obtain access token from GitHub. Please try again."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                token_data = response.json()
                if 'error' in token_data:
                    return Response({
                        "status": "failed",
                        "message": f"GitHub error: {token_data.get('error_description', token_data['error'])}"
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
                    return Response({
                        "status": "failed",
                        "message": "Failed to get user info from GitHub. Please try again."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                github_data = response.json()
                
                # Get user's email (GitHub may not provide email in user data)
                email_response = requests.get(
                    'https://api.github.com/user/emails',
                    headers={
                        'Authorization': f'token {access_token}',
                        'Accept': 'application/json'
                    }
                )
                
                if email_response.status_code != 200:
                    return Response({
                        "status": "failed",
                        "message": "Failed to get email from GitHub. Please ensure your GitHub account has a verified email."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                emails = email_response.json()
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
                
                # Check auth provider
                if user.auth_provider != 'github':
                    return Response({
                        "status": "failed",
                        "message": f"This email is already registered with {user.auth_provider}. Please use that login method."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Update GitHub ID if not set
                if not user.auth_id:
                    user.auth_id = str(github_data.get('id'))
                    user.save()
                
                if not user.is_active:
                    return Response({
                        "status": "failed",
                        "message": "This account has been deactivated."
                    }, status=status.HTTP_401_UNAUTHORIZED)
                
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
