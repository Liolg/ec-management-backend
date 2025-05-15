from django.contrib import admin

from .models import EcAccount, DailyEntry

admin.site.register( EcAccount )
admin.site.register( DailyEntry )
