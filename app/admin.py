from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Tag)
admin.site.register(Profile)
admin.site.register(LikeQuestion)
admin.site.register(LikeAnswer)
admin.site.register(DislikeQuestion)
admin.site.register(DislikeAnswer)