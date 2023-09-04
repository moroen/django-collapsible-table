from django import template

from django.utils.html import format_html
from django.conf import settings

register = template.Library()


@register.simple_tag
def material_icons():
    return format_html(
        f'<link href="https://fonts.googleapis.com/icon?family=Material+Icons" rel="stylesheet">'
    )


@register.simple_tag
def bootstrap_icons():
    return format_html(
        f'<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">'
    )
