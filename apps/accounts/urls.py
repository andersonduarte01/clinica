from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html')),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    #path('password_change/', auth_views.PasswordChangeView.
         #as_view(template_name='registration/password_change_form.html')),
    #path('password_change/done/', auth_views.PasswordChangeDoneView.
         #as_view(template_name='registration/password_change_done.html')),
    #path('password_reset/', auth_views.PasswordResetView.
         #as_view(template_name='registration/password_reset_form.html')),
    #path('password_reset/done/', auth_views.PasswordResetDoneView.
         #as_view(template_name='registration/password_reset_done.html')),
    #path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.
         #as_view(template_name='password_reset_confirm.html')),
    #path('reset/done/', auth_views.PasswordResetCompleteView.
         #as_view(template_name='registration/password_reset_complete.html')),
]