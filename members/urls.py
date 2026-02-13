from django.urls import path
from . import views
from .views import MemberLoginView,  MemberListView, MemberCreateView, MemberUpdateView, PermissionDashboardView,verify_email, index,  resend_verification_email
from django.contrib.auth import views as auth_views
from members.forms import EmailOrAliasAuthenticationForm

urlpatterns = [
    path('',views.index, name='index'),
    path("members/", MemberListView.as_view(), name="member-list"),
    path("members/add/", MemberCreateView.as_view(), name="member-add"),
    path("members/<int:pk>/edit/", MemberUpdateView.as_view(), name="member-edit"),
    path("verify-email/<uuid:token>/", verify_email, name="verify-email"),
    path("login/", MemberLoginView.as_view(authentication_form=EmailOrAliasAuthenticationForm),name="login",),
    path("resend-verification/", resend_verification_email, name="resend-verification"),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("password-reset/",auth_views.PasswordResetView.as_view(),name="password_reset",),
    path("password-reset/done/",auth_views.PasswordResetDoneView.as_view(),name="password_reset_done",),
    path("reset/<uidb64>/<token>/",auth_views.PasswordResetConfirmView.as_view(),name="password_reset_confirm",),
    path("reset/done/",auth_views.PasswordResetCompleteView.as_view(),name="password_reset_complete",),

    path("permissions/", PermissionDashboardView.as_view(), name="permission-dashboard"),
]
