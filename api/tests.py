from rest_framework.test import APITestCase
from blog.models import Article, Comment
from django.urls import reverse
from rest_framework import status
from django.utils.text import slugify
from django.contrib.auth import get_user_model
from unidecode import unidecode
from django.utils import timezone

# Перед проведением тестов не забудьте поменять настройки кеширования в settings на dummycache

def article_create(author, title, body, status, slug):
    return Article.objects.create(author=author, title=title,
                                  body=body, status=status, slug=slug)

def comment_create(author, body, article):
    return Comment.objects.create(author=author, article=article, body=body)

def user_create():
    return get_user_model().objects.create_user(username='test', password='qowieuryt')    


class APITests(APITestCase):
    title = 'article_test'
    body = 'something...'
    slug = slugify(unidecode(title))
    status = 'PB'

    def SetUp(self):
        self.user = user_create()
        self.article_df = article_create(author=self.user, title=self.title, body=self.body, status='DF', slug=self.slug+'2')
        self.article_pb1 = article_create(author=self.user, title=self.title, body=self.body, status=self.status, slug=self.slug)
        self.article_pb2 = article_create(author=self.user, title=self.title, body=self.body, status=self.status, slug=self.slug+'1')

    def test_article_list(self):
        self.SetUp()
        url = reverse('api:article_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self.assertNotIn(self.article_df, response.data)

    def test_article_pb_detail(self):
        self.SetUp()
        url = reverse('api:article_detail', args=(self.article_pb1.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('comments', response.data)
        self.assertEqual(response.data['author'], self.article_pb1.author.username)
        self.assertEqual(response.data['title'], self.article_pb1.title)
        self.assertEqual(response.data['body'], self.article_pb1.body)
        self.assertEqual(response.data['slug'], self.article_pb1.slug)

    def test_article_df_detail(self):
        self.SetUp()
        url = reverse('api:article_detail', args=(self.article_df.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_article_df_detail_for_author(self):
        self.SetUp()
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        url = reverse('api:article_detail', args=(self.article_df.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('comments', response.data)
        self.assertEqual(response.data['author'], self.article_df.author.username)
        self.assertEqual(response.data['title'], self.article_df.title)
        self.assertEqual(response.data['body'], self.article_df.body)
        self.assertEqual(response.data['slug'], self.article_df.slug)

    def test_article_create(self):
        user = user_create()
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        data = {
            'title': self.title,
            'body': self.body,
            'status': self.status,
            'slug': self.slug,
        }
        url = reverse('api:article_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], data['title'])
        self.assertEqual(response.data['slug'], data['slug'])
        self.assertEqual(response.data['body'], data['body'])
        self.assertEqual(response.data['status'], data['status'])

    def test_article_delete_successful(self):
        self.SetUp()
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        url = reverse('api:article_delete', args=(self.article_pb1.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        url = reverse('api:article_detail', args=(self.article_pb1.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_article_delete_forbidden(self):
        self.SetUp()
        self.user2 = get_user_model().objects.create_user(username='test22', password='qowieuryt')
        is_authenticated = self.client.login(username='test22', password='qowieuryt')
        self.assertTrue(is_authenticated)
        url = reverse('api:article_delete', args=(self.article_pb1.id, ))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        url = reverse('api:article_detail', args=(self.article_pb1.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_comment_create_successful(self):
        self.SetUp()
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        data = {
            'body': 'Some comment'
        }
        url = reverse('api:comment_create', args=(self.article_pb1.id, ))
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        url = reverse('api:article_detail', args=(self.article_pb1.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['comments']), 1)
        self.assertEqual(response.data['comments'][0], {'author': self.user.username, 'body': 'Some comment'})
    
    def test_comment_create_forbidden(self):
        self.SetUp()
        url = reverse('api:comment_create', args=(self.article_pb1.id, ))
        data = {
            'body': 'Some comment'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_create_for_draft_article(self):
        self.SetUp()
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        url = reverse('api:comment_create', args=(self.article_df.id, ))
        data = {
            'body': 'Some comment'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_comment_delete_successful(self):
        self.SetUp()
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        comment = comment_create(author=self.user, body='Test', article=self.article_pb1)
        url = reverse('api:comment_delete', args=(comment.id, ))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_comment_delete_forbidden(self):
        self.SetUp()
        user2 = get_user_model().objects.create_user(username='test22', password='qowieuryt')
        is_authenticated = self.client.login(username='test22', password='qowieuryt')
        self.assertTrue(is_authenticated)
        comment = comment_create(author=self.user, body='Test', article=self.article_pb1)
        url = reverse('api:comment_delete', args=(comment.id, ))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_user_list(self):
        self.SetUp()
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        url = reverse('api:user_list')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['id'], self.user.id)
        self.assertEqual(response.data[0]['username'], self.user.username)
        self.assertEqual(response.data[0]['first_name'], self.user.first_name)
        self.assertEqual(response.data[0]['last_name'], self.user.last_name)
        self.assertQuerySetEqual(response.data[0]['comments_published'], self.user.comments_published.all())