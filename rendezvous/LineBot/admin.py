from django.contrib import admin
from .models import Reservation, Location, User, Announcement, Report


admin.site.register(Reservation)
admin.site.register(Location)
admin.site.register(User)
admin.site.register(Announcement)
admin.site.register(Report)