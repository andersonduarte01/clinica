from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.serializers import CustomTokenObtainPairSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    """Login JWT com payload enriquecido (tenant, role, módulos)."""
    serializer_class = CustomTokenObtainPairSerializer
