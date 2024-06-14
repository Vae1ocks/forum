from django.http import Http404
from blog.models import Article, Comment
from django.contrib.auth import get_user_model
from rest_framework import generics
from django.db.models import Q
from . import serializers
from django.contrib.auth import get_user_model
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAuthor
from django.utils import timezone
from django.utils.text import slugify
from unidecode import unidecode
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator


@method_decorator(cache_page(60 * 15), name='dispatch')
class ArticleList(generics.ListAPIView):
    serializer_class = serializers.ArticleListSerializer

    def get_queryset(self):
        user = self.request.user
        return Article.objects.filter(Q(status='PB') | Q(author__username=user)).select_related('author').prefetch_related('tags')


@method_decorator(cache_page(60 * 15), name='dispatch')
class ArticleDetail(generics.RetrieveAPIView):
    serializer_class = serializers.ArticleSerializer

    def get_queryset(self):
        user = self.request.user
        return Article.objects.filter(Q(status='PB') | Q(author__username=user))
    

class ArticleCreate(generics.CreateAPIView):
    serializer_class = serializers.ArticleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user, publish=timezone.now(),
                        slug=slugify(unidecode(serializer.validated_data['title'])))


class ArticleDelete(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated, IsAuthor]
    queryset = Article.objects.all()


@method_decorator(cache_page(60 * 15), name='dispatch')
class UserList(generics.ListAPIView):
    serializer_class = serializers.UserSerializer
    queryset = get_user_model().objects.all().prefetch_related('comments_published')


class CommentCreate(generics.CreateAPIView):
    serializer_class = serializers.CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        article_id = self.kwargs.get('article_id')
        try:
            article = Article.published.get(id=article_id)
        except:
            raise Http404
        serializer.save(article=article, author=self.request.user)


class CommentDelete(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self): # если без permissions.IsAuthor
        return Comment.objects.filter(author=self.request.user)