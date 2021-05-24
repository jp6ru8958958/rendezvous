from django.db import models

class reservation(models.Model):
    location = models.CharField(max_length=100)
    line_user_id = models.IntegerField()
    reservation_time = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

class location(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=100)
    link = models.URLField()
    description = models.CharField(max_length=300, blank=True)
    tel = models.CharField(max_length=10, blank=True)

class user(models.Model):
    line_user_id = models.CharField(max_length=40)
    real_name = models.CharField(max_length=40)
    operation_status = models.CharField(max_length=20, default='Normal')