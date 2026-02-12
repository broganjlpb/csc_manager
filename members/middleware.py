from django.shortcuts import redirect
from django.urls import reverse

class RequireVerifiedEmailMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user

        if (
            user.is_authenticated
            and not user.email_verified
            and request.path not in [
                reverse("login"),
                reverse("verify-email"),
            ]
        ):
            return redirect("login")

        return self.get_response(request)
