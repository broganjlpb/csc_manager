from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse

from django.contrib.auth.views import LoginView
from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required
from members.forms import ResendVerificationEmailForm
from members.utils import send_verification_email
from .models import EmailVerificationToken

class MemberLoginView(LoginView):
    redirect_authenticated_user = True


    

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