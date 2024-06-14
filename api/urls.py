from django.urls import path, include
from . import views

app_name = 'api'

urlpatterns = [
    path('', views.ArticleList.as_view(), name='article_list'),
    path('<int:pk>/', views.ArticleDetail.as_view(), name='article_detail'),
    path('article/create/', views.ArticleCreate.as_view(), name='article_create'),
    path('article/<int:pk>/delete/', views.ArticleDelete.as_view(), name='article_delete'),
    path('article/<int:article_id>/comment/create/', views.CommentCreate.as_view(), name='comment_create'),
    path('comment/<int:pk>/delete/', views.CommentDelete.as_view(), name='comment_delete'),
    path('user/', views.UserList.as_view(), name='user_list'),
]
