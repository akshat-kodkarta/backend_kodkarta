from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views.views import (
    HealthCheckView,
    UserRegistrationView,
    GoogleLoginView,
    GithubLoginView,
    UserProfileView,
    LogoutView,
    EmailLoginView
)

urlpatterns = [
    # Health check
    path('status/', HealthCheckView.as_view(), name='health_check'),

    # Registration and authentication
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', EmailLoginView.as_view(), name='email_login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('refresh-token/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Social auth
    path('login/google/', GoogleLoginView.as_view(), name='google_login'),
    path('login/github/', GithubLoginView.as_view(), name='github_login'),
    
    # User profile
    path('profile/', UserProfileView.as_view(), name='user_profile'),
]
