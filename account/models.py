from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext as _


class User(AbstractUser):
    avatar = models.ImageField(upload_to='users/%Y/%m/%d/', blank=True, null=True)
    about_self = models.CharField(max_length=300, blank=True, null=True)
    email = models.EmailField(_("email address"), unique=True)
    user_updated = models.DateTimeField(auto_now=True)