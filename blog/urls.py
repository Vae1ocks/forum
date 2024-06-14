from django.urls import path
from . import views
from .feeds import LatestArticlesFeed

app_name = 'blog'

urlpatterns = [
    path('', views.ArticleListView.as_view(), name='article_list'),
    path('tag/<slug:tag>/', views.ArticleListView.as_view(), name='article_tagged_list'),
    path('article-detail/<slug:slug>/<int:id>/', views.ArticleDetailView.as_view(), name='article_detail'),
    path('article-comment/<int:id>/', views.comment_create, name='article_comment'),
    # path('feed/', LatestArticlesFeed(), name='feed'),
    path('search/', views.ArticleSearchView.as_view(), name='article_search'),
    path('article/create/', views.ArticleCreateView.as_view(), name='article_create'),
    path('article/edit/<int:pk>/', views.ArticleEditView.as_view(), name='article_edit'),
    path('article/delete/<int:pk>/', views.ArticleDeleteView.as_view(), name='article_delete'),
    path('comment/<int:comment_id>/delete/', views.CommentDeleteView.as_view(), name='comment_delete')
]