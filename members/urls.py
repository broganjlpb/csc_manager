from django.urls import path
from . import views
from .views import verify_email, index, MemberLoginView, resend_verification_email
from django.contrib.auth import views as auth_views
from members.forms import EmailOrAliasAuthenticationForm

urlpatterns = [
    path('',views.index, name='index'),
    path("verify-email/<uuid:token>/", verify_email, name="verify-email"),
    path("login/", MemberLoginView.as_view(authentication_form=EmailOrAliasAuthenticationForm),name="login",),
    path("resend-verification/", resend_verification_email, name="resend-verification"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/",auth_views.PasswordResetView.as_view(),name="password_reset",),
    path("password-reset/done/",auth_views.PasswordResetDoneView.as_view(),name="password_reset_done",),
    path("reset/<uidb64>/<token>/",auth_views.PasswordResetConfirmView.as_view(),name="password_reset_confirm",),
    path("reset/done/",auth_views.PasswordResetCompleteView.as_view(),name="password_reset_complete",),
]
