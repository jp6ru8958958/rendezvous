from django.db import models

class Reservation(models.Model):
    location = models.CharField(max_length=100)
    line_user_id = models.CharField(max_length=40)
    reservation_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class Location(models.Model):
    name = models.CharField(max_length=100)
    official_website_link = models.URLField(default='')
    tel = models.CharField(max_length=10, blank=True)
    address = models.CharField(max_length=100)
    maps_link = models.URLField(default='')
    description = models.CharField(max_length=300, blank=True)

class User(models.Model):
    line_user_id = models.CharField(max_length=40)
    real_name = models.CharField(max_length=40)
    operation_status = models.CharField(max_length=50, default='Normal')

class Announcement(models.Model):
    author = models.CharField(max_length=40)
    content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)

class Report(models.Model):
    author = models.CharField(max_length=40)
    content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)