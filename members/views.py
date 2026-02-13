from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.db.models import Q

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, CreateView, UpdateView
from members.forms import ResendVerificationEmailForm, MemberForm
from members.utils import send_verification_email
from .models import EmailVerificationToken, Member
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import TemplateView
from django.contrib.auth import get_user_model

User = get_user_model()

class PermissionDashboardView(UserPassesTestMixin, TemplateView):
    template_name = "members/permission_dashboard.html"

    def test_func(self):
        return self.request.user.is_staff

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        users = User.objects.all().prefetch_related(
            "groups__permissions",
            "user_permissions"
        )

        dashboard = []

        for user in users:
            perm_map = {}

            # direct permissions
            for perm in user.user_permissions.all():
                key = perm.id
                perm_map.setdefault(key, {
                    "perm": perm,
                    "direct": False,
                    "groups": []
                })
                perm_map[key]["direct"] = True

            # group permissions
            for group in user.groups.all():
                for perm in group.permissions.all():
                    key = perm.id
                    perm_map.setdefault(key, {
                        "perm": perm,
                        "direct": False,
                        "groups": []
                    })
                    perm_map[key]["groups"].append(group)

            dashboard.append({
                "user": user,
                "permissions": perm_map.values(),
            })

        context["dashboard"] = dashboard
        return context

class MemberLoginView(LoginView):
    redirect_authenticated_user = True


class MemberListView(ListView):
    model = Member
    template_name = "members/member_list.html"
    context_object_name = "members"
    ordering = ["email"]  
    paginate_by = 10   # ⭐ number per page 

    def get_queryset(self):
        qs = super().get_queryset()

        search = self.request.GET.get("q")

        if search:
            qs = qs.filter(
                Q(email__icontains=search) |
                Q(username__icontains=search) |
                Q(full_name__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )

        return qs


class MemberCreateView(CreateView):
    model = Member
    form_class = MemberForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("member-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add Member"
        context["submit_text"] = "Create"
        context["cancel_url"] = reverse_lazy("member-list")
        return context

class MemberUpdateView(UpdateView):
    model = Member
    form_class = MemberForm
    template_name = "forms/form_page.html"
    success_url = reverse_lazy("member-list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit {self.object.get_short_name()}"
        context["submit_text"] = "Save changes"
        context["cancel_url"] = reverse_lazy("member-list")
        return context




def verify_email(request, token):
    verification = get_object_or_404(EmailVerificationToken, token=token)

    user = verification.user
    user.email_verified = True
    user.save()

    verification.delete()

    return HttpResponse("Your email has been verified successfully.")

def index(request):
    # return HttpResponse("Index Page")
    return render( request, "index.html",)

def resend_verification_email(request):
    if request.method == "POST":
        form = ResendVerificationEmailForm(request.POST)
        if form.is_valid():
            send_verification_email(request, form.user)
            return render(
                request,
                "members/resend_verification_sent.html",
            )
    else:
        form = ResendVerificationEmailForm()

    return render(
        request,
        "members/resend_verification.html",
        {"form": form},
    )