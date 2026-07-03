from django import template
from django.conf import settings

register = template.Library()

@register.filter
def cover_url(song):
    if song.cover_image:
        return song.cover_image.url
    return '/static/images/eratunez-logo.png'