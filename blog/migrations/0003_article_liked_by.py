# Generated by Django 4.2.8 on 2024-05-17 19:10

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('blog', '0002_remove_comment_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='article',
            name='liked_by',
            field=models.ManyToManyField(blank=True, related_name='articles_liked', to=settings.AUTH_USER_MODEL),
        ),
    ]
