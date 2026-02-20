from django import template
from races.services import calculate_points, format_seconds

register = template.Library()

@register.filter
def points(position):
    return calculate_points(position)

@register.filter
def format_time(value):
    if value is None:
        return ""
    return format_seconds(value)
