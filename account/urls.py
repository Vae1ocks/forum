from django.urls import path, include, reverse_lazy
from . import views
from django.contrib.auth import views as auth_views

app_name = 'account'

urlpatterns = [
    path('login/', views.RedirectLoginView.as_view(), name='login'),
    path('logout/', views.RedirectLogoutView.as_view(), name='logout'),

    path('password_change/', auth_views.PasswordChangeView.as_view(
        success_url=reverse_lazy('account:password_change_done')
    ), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(), name='password_change_done'),

    path('password_reset/', auth_views.PasswordResetView.as_view(
        success_url=reverse_lazy('account:password_reset_done')
    ), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        success_url=reverse_lazy('account:password_reset_complete')
    ), name='password_reset_confirm'),

    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('registration/', views.RegistrationView.as_view(), name='registration'),
    path('registration/confirmation/', views.RegistrationConfirmation.as_view(), name='registration_confirmation'),
    path('registration/done/', views.RegistrationDoneView.as_view(), name='registration_done'),
    path('profile/<int:pk>/', views.UserDetailView.as_view(), name='user_detail'),
    path('profile/edit/<int:pk>/', views.UserEditView.as_view(), name='edit'),
    path('email-edit/', views.OldEmailConfirmationView.as_view(), name='old_email_confirmation'),
    path('email-edit/new_email/<str:redirect_token>', views.NewEmailEnterView.as_view(), name='new_email_enter'),
    path('email-edit/new-email-confirmation/', views.NewEmailConfirmation.as_view(), name='new_email_confirmation'),
    path('secret-get/password-confirmation/', views.TokenCreateView.as_view(), name='create_authentication_token'),
    path('token-get/info/', views.TokenInfoView.as_view(), name='authentication_token_info'),
    path('secret-key/login', views.TokenLoginView.as_view(), name='authentication_token_login'),
]
