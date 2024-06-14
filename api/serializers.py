from rest_framework import serializers
from blog.models import Article, Comment
from taggit.models import Tag
from django.contrib.auth import get_user_model


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    class Meta:
        model = Comment
        fields = ['author', 'body']
        

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['name']


class ArticleListSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    author = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = Article
        fields = ['id', 'author', 'title', 'publish',
                  'updated', 'tags']


class ArticleSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    author = serializers.ReadOnlyField(source='author.username')
    
    class Meta:
        model = Article
        fields = ['id', 'author', 'title', 'slug', 'body', 'publish',
                  'updated', 'status', 'comments', 'tags']



class UserSerializer(serializers.ModelSerializer):
    comments_published = CommentSerializer(many=True, read_only=True)

    class Meta:
        model = get_user_model()
        fields = ['id', 'username', 'first_name', 'last_name',
                  'email', 'date_joined', 'about_self', 'comments_published']