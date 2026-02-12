import uuid
from django.urls import reverse
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from members.models import EmailVerificationToken


def send_verification_email(request, user):
    token_obj, created = EmailVerificationToken.objects.get_or_create(
        user=user,
        defaults={"token": uuid.uuid4()},
    )

    token = str(token_obj.token)

    verify_url = request.build_absolute_uri(
        reverse("verify-email", args=[token])
    )

    subject = "Verify your email address"

    text_content = render_to_string(
        "emails/verify_email.txt",
        {"verify_url": verify_url, "user": user},
    )

    html_content = render_to_string(
        "emails/verify_email.html",
        {"verify_url": verify_url, "user": user},
    )

    email = EmailMultiAlternatives(
        subject,
        text_content,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )

    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)
