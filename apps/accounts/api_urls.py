from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView, TokenBlacklistView

from apps.accounts.views import CustomTokenObtainPairView

urlpatterns = [
    # POST /api/v1/auth/token/          → login, retorna access + refresh
    path("token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    # POST /api/v1/auth/token/refresh/  → renova access token via refresh
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # POST /api/v1/auth/token/blacklist/ → logout, invalida refresh token
    path("token/blacklist/", TokenBlacklistView.as_view(), name="token_blacklist"),
]
