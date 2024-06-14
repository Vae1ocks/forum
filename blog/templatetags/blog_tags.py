from django import template
from ..models import Article
from taggit.models import Tag
from django.utils.safestring import mark_safe
import markdown


register = template.Library()

@register.simple_tag
def all_articles():
    return Article.published.count()

@register.simple_tag
def all_tags():
    return Tag.objects.values_list('name', flat=True)

@register.filter(name='markdown')
def markdown_into_html(text):
    return mark_safe(markdown.markdown(text))