from django.contrib import admin
from .models import Reservation, Location, User, Message


admin.site.register(Reservation)
admin.site.register(Location)
admin.site.register(User)
admin.site.register(Message)