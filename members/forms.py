
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.core.exceptions import ValidationError

class EmailOrAliasAuthenticationForm(AuthenticationForm):
    username = forms.CharField(label="Email or Alias")

    def confirm_login_allowed(self, user):
        if not user.email_verified:
            raise ValidationError(
                "Your email address is not verified. Click on the 'Resend verification email link' below and request a new verification link",
                code="email_not_verified",
            )

class ResendVerificationEmailForm(forms.Form):
    email = forms.EmailField(label="Email address")

    def clean_email(self):
        email = self.cleaned_data["email"].lower()

        from members.models import Member
        try:
            user = Member.objects.get(email__iexact=email)
        except Member.DoesNotExist:
            raise forms.ValidationError("No account found with this email.")

        if user.email_verified:
            raise forms.ValidationError("This email is already verified.")

        self.user = user
        return email