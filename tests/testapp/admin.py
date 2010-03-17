from django.contrib import admin

from models import *

class PersonOptions(admin.ModelAdmin):
    pass

class TitleOptions(admin.ModelAdmin):
    pass

class ClipOptions(admin.ModelAdmin):
    pass


admin.site.register(Person, PersonOptions)
admin.site.register(Title, TitleOptions)
admin.site.register(Clip, ClipOptions)