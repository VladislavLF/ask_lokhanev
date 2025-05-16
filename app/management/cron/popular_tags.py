from app.models import *
from django.core.cache import cache

def update_popular_tags() -> None:
    object_list = Tag.objects.all()
    cache.set('popular_tags', object_list.annotate(num_questions=Count('question')).order_by('-num_questions')[:20], 3600 * 24 * 31 * 3.1)