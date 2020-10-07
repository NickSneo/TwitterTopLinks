from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class tweetsDB(models.Model):
    user = models.CharField(blank=False, max_length=20)
    tweet_id = models.IntegerField(blank=False)
    tweet_text = models.TextField(blank=False)
    tweeted_user = models.CharField(blank=False, max_length=20)
    date_time = models.DateTimeField(auto_now=False, auto_now_add=False)


class urlsDB(models.Model):
    user = models.CharField(blank=False, max_length=20)
    tweeted_user = models.CharField(blank=False, max_length=20)
    url = models.URLField(blank=False, max_length=200)
    domain = models.CharField(blank=False, max_length=20)
