from django.conf import settings

def template_settings(request):
    """
    Expose whitelisted settings to templates.
    Never expose secrets here.
    """
    return {
        name: getattr(settings, name)
        for name in getattr(settings, "TEMPLATE_VISIBLE_SETTINGS", [])
    }