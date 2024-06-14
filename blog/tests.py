from django.test import TestCase
from django.contrib.auth import get_user_model
from blog.models import Article, Comment
from django.urls import reverse
from django.utils.text import slugify
from taggit.models import Tag
import redis
from django.conf import settings

# Перед проведением тестов не забудьте поменять настройки кеширования в settings на dummycache

def article_create(author, title, body, status, slug):
    return Article.objects.create(author=author, title=title,
                                  body=body, status=status, slug=slug)

def comment_create(author, body, article):
    return Comment.objects.create(author=author, article=article, body=body)

def user_create():
    return get_user_model().objects.create_user(username='test', password='qowieuryt')    

def redis_create():
    return redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

class ArticleTest(TestCase):
    title = 'article_test'
    slug = slugify(title)
    body = 'something...'
    status = 'DF'

    def test_article_list(self):
        self.user = user_create()
        article_df = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status=self.status)
        article_pb = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status='PB')
        response = self.client.get(reverse('blog:article_list'))
        
        all_articles = response.context['all_articles']

        self.assertTemplateUsed(response, 'blog/article/list.html')
        self.assertIn('articles', response.context)
        self.assertIn('all_articles', response.context)
        self.assertIn('all_tags', response.context)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(all_articles, Article.published.count())
        self.assertNotIn(article_df, response.context['articles'])
        self.assertQuerySetEqual(response.context['articles'], [article_pb])


    def test_article_pb_detail(self):
        self.user = user_create()
        article_pb = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status='PB')
        url = reverse('blog:article_detail', args=(article_pb.slug, article_pb.id))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'blog/article/article_detail.html')
        self.assertEqual(article_pb.author, self.user)
        self.assertEqual(article_pb.title, self.title)
        self.assertEqual(article_pb.body, self.body)
        self.assertEqual(article_pb.status, 'PB')
        self.assertIsNotNone(article_pb.publish)
        self.assertIsNotNone(article_pb.created)

    def test_article_df_detail(self):
        self.user = user_create()
        article_df = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status=self.status)
        url = reverse('blog:article_detail', args=(article_df.slug, article_df.id))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

        is_login_successful = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_login_successful)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_article_and_same_tags(self):
        self.user = user_create()
        article_pb = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status='PB')
        article1 = article_create(author=self.user, title=self.title, body=self.body, slug=self.slug+'1', status='PB')
        article2_df = article_create(author=self.user, title=self.title, slug=self.slug+'2', body=self.body, status=self.status)
        article2 = article_create(author=self.user, title=self.title, slug=self.slug+'3', body=self.body, status='PB')
        article3 = article_create(author=self.user, title=self.title, slug=self.slug+'4', body=self.body, status='PB')
        article4 = article_create(author=self.user, title=self.title, slug=self.slug+'5', body=self.body, status='PB')
        article5 = article_create(author=self.user, title=self.title, slug=self.slug+'6', body=self.body, status='PB')
        article6_extra = article_create(author=self.user, title=self.title, slug=self.slug+'7', body=self.body, status='PB')
        articles_with_same_tags = [article1, article2, article3, article4, article5]
        url = reverse('blog:article_detail', args=(article_pb.slug, article_pb.id))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

    def test_with_comment(self):
        self.user = user_create()
        article_pb = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status='PB')
        article_df = article_create(author=self.user, title=self.title, slug=self.slug+'1', body=self.body, status=self.status)
        comment_for_pb = comment_create(author=self.user, article=article_pb, body=self.body)
        url = reverse('blog:article_detail', args=(article_pb.slug, article_pb.id))
        response = self.client.get(url)

        self.assertQuerysetEqual(response.context['comments'], [comment_for_pb])

        url = reverse('blog:article_detail', args=(article_df.slug, article_df.id))
        response = self.client.get(url)

        self.assertEqual(response.status_code, 404)

    def test_article_delete_success(self):
        self.user = user_create()
        article = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status='PB')
        url = reverse('blog:article_delete', args=(article.id, ))

        is_login_successful = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_login_successful)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        
    def test_article_delete_no_permission(self):
        self.user = user_create()
        self.user2 = get_user_model().objects.create_user(username='Test2', password='alskdjfhg')
        article_by_user = article_create(author=self.user, title=self.title, slug=self.slug, body=self.body, status='PB')
        url = reverse('blog:article_delete', args=(article_by_user.id, ))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

        is_login_successful = self.client.login(username='Test2', password='alskdjfhg')
        self.assertTrue(is_login_successful)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.post(url)
        self.assertEqual(response.status_code, 404)

    def test_search_articles(self):
        self.user = user_create()
        article1 = article_create(author=self.user, title='music', slug=self.slug+'1', body=self.body, status='PB')
        article2 = article_create(author=self.user, title='musician', slug=self.slug+'3', body=self.body, status='PB')
        article3 = article_create(author=self.user, title='musicality', slug=self.slug+'2', body=self.body, status='PB')
        query = {'query': 'music'}

        url = reverse('blog:article_search')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.get(url, query)
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['results'], [article1, article2, article3])

    def test_article_edit(self):
        self.user = user_create()
        article = article_create(author=self.user, title='music', slug=self.slug, body=self.body, status='PB')
        url = reverse('blog:article_edit', args=(article.id, ))
        data = {
            'title': 'New Title',
            'body': 'New Body',
        }
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)

    def article_edit_no_permission(self):
        self.user = user_create()
        self.user2 = get_user_model().objects.create_user(username='Test2', password='alskdjfhg')
        article = article_create(author=self.user, title='music', slug=self.slug, body=self.body, status='PB')
        url = reverse('blog:article_edit', args=(article.id, ))
        data = {
            'title': 'New Title',
            'body': 'New Body',
        }
        is_authenticated = self.client.login(username='Test2', password='alskdjfhg')
        self.assertTrue(is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 404)

    def test_comment_delete_successful(self):
        self.user = user_create()
        article = article_create(author=self.user, title='music', slug=self.slug, body=self.body, status='PB')
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        comment = comment_create(author=self.user, body='Test', article=article)
        url = reverse('blog:comment_delete', args=(comment.id, ))
        response = self.client.delete(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['article'], article)
        self.assertQuerySetEqual(response.context['comments'], [])

    def test_comment_delete_forbidden(self):
        self.user = user_create()
        article = article_create(author=self.user, title='music', slug=self.slug, body=self.body, status='PB')
        user2 = get_user_model().objects.create_user(username='test22', password='qowieuryt')
        is_authenticated = self.client.login(username='test22', password='qowieuryt')
        self.assertTrue(is_authenticated)
        comment = comment_create(author=self.user, body='Test', article=article)
        url = reverse('blog:comment_delete', args=(comment.id, ))
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 404)

        url = reverse('blog:article_detail', args=(article.slug, article.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['comments'], [comment])

    def test_comment_create(self):
        self.user = user_create()
        article = article_create(author=self.user, title='music', slug=self.slug, body=self.body, status='PB')
        data = {
            'body': 'Body of the comment'
        }
        is_authenticated = self.client.login(username='test', password='qowieuryt')
        self.assertTrue(is_authenticated)
        url = reverse('blog:article_comment', args=(article.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 405)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        url = reverse('blog:article_detail', args=(article.slug, article.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['comments']), 1)
        self.assertEqual(response.context['comments'][0].body, data['body'])

    def test_comment_create_forbidden(self):
        self.user = user_create()
        article = article_create(author=self.user, title='music', slug=self.slug, body=self.body, status='PB')
        data = {
            'body': 'Body of the comment'
        }
        url = reverse('blog:article_comment', args=(article.id, ))
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('registration/login.html')
        url = reverse('blog:article_detail', args=(article.slug, article.id))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context['comments'], [])