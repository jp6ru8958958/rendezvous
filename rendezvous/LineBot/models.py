from django.db import models

class Reservation(models.Model):
    location = models.CharField(max_length=100)
    line_user_id = models.IntegerField()
    reservation_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class Location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    link = models.URLField()
    description = models.CharField(max_length=300, blank=True)
    tel = models.CharField(max_length=10, blank=True)

class User(models.Model):
    line_user_id = models.CharField(max_length=40)
    real_name = models.CharField(max_length=40)
    operation_status = models.CharField(max_length=20, default='Normal')

class Message(models.Model):
    author = models.CharField(max_length=40)
    content = models.TextField(null=False)
    created_at = models.DateTimeField(auto_now_add=True)