from django import template
from django.core.cache import cache

register = template.Library()

@register.simple_tag()
def get_popular_tags():
    return cache.get('popular_tags', [])

@register.simple_tag()
def get_top_users():
    return cache.get('top_users', [])
