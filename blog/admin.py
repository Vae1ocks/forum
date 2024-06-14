from django.contrib import admin
from .models import Article, Comment


class CommentInLine(admin.StackedInline):
    model = Comment

@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ['author', 'title', 'slug', 'body', 'created', 'updated', 'publish', 'status']
    prepopulated_fields = {'slug': ('title', )}
    search_fields = ['title', 'author__username']
    list_filter = ['created', 'publish']
    inlines = [CommentInLine]
    filter_horizontal = ('tags',)