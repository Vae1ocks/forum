from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.urls import reverse
from taggit.managers import TaggableManager
from django.utils.translation import gettext_lazy as _


class IsPublished(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(status=Article.Status.PUBLISHED)


class Article(models.Model):
    
    class Status(models.TextChoices):
        DRAFT = 'DF', _('Draft')
        PUBLISHED = 'PB', _('Published')

    title = models.CharField(max_length=250)
    slug = models.CharField(max_length=250)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    publish = models.DateTimeField(default=timezone.now)
    author = models.ForeignKey(get_user_model(),
                               on_delete=models.CASCADE,    
                               related_name='articles')
    all_objects = models.Manager()
    published = IsPublished()
    status = models.CharField(max_length=2,
                              choices=Status.choices,
                              default=Status.DRAFT)
    objects = models.Manager()
    tags = TaggableManager()
    

    class Meta:
        ordering = ['-publish']
        indexes = [
            models.Index(fields=['-publish'])
        ]

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('blog:article_detail', args=[self.slug, self.id])


class Comment(models.Model):
    author = models.ForeignKey(get_user_model(),
                               related_name='comments_published',
                               on_delete=models.CASCADE)
    article = models.ForeignKey(Article,
                             related_name='comments',
                             on_delete=models.CASCADE)
    body = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created']
        indexes = [
            models.Index(fields=['-created'])
        ]
    
    def __str__(self):
        return self.body
