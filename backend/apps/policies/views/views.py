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
