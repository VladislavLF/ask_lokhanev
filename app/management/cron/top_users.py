from app.models import *
from django.core.cache import cache

def update_top_users() -> None:
    top_users = Profile.objects.all().order_by('-rating')[:10]
    cache.set('top_users', top_users, 3600 * 24 * 7.1)