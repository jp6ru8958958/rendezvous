from django.contrib import admin
from .models import reservation, location, user


admin.site.register(reservation)
admin.site.register(location)
admin.site.register(user)