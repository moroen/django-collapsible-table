from django import template

from django.utils.html import format_html
from django.conf import settings

register = template.Library()


@register.simple_tag
def material_icons():
    return format_html(
        f'<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">'
    )
