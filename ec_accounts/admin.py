from django.contrib import admin

from .models import EcAccount, DailyEntry, EcAccountEntry

admin.site.register( EcAccount )
admin.site.register( DailyEntry )
admin.site.register( EcAccountEntry )
