from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

# Перед проведением тестов не забудьте поменять настройки кеширования в settings на dummycache

def user_create(username, password, email=''):
    return get_user_model().objects.create_user(username=username, password=password, email=email)


class UserTest(TestCase):
    username = 'Test'
    password = 'alskdjfhg'

    def test_registration(self):
        from django.core.mail import outbox # если глобально импортировать, то outbox = []
        url = reverse('account:registration')
        data = {
            'username': 'Test',
            'password': 'qpwoeiruty',
            'password_repeat': 'qpwoeiruty',
            'email': 'test@gmail.com'
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/email_code_confirmation.html')

        self.assertEqual(len(outbox), 1)
        message = outbox[0]
        confirmation_code = message.body[-6:]

        url = reverse('account:registration_confirmation')
        self.assertEqual(message.to, [data['email']])
        response = self.client.post(url, {'confirmation_code': confirmation_code}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/registration_done.html')

        self.assertEqual(get_user_model().objects.count(), 1)
        is_authenticated = self.client.login(username=data['username'], password=data['password'])
        self.assertTrue(is_authenticated)

    def test_registration_code_not_valid(self):
        url = reverse('account:registration')
        data = {
            'username': 'Test',
            'password': 'qpwoeiruty',
            'password_repeat': 'qpwoeiruty',
            'email': 'test@gmail.com'
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/email_code_confirmation.html')

        not_valid_confirmation_code = 999999

        response = self.client.post(url, {'confirmation_code': not_valid_confirmation_code})
        self.assertEqual(response.status_code, 200)

        self.assertEqual(get_user_model().objects.count(), 0)
        is_authenticated = self.client.login(username=data['username'], password=data['password'])
        self.assertFalse(is_authenticated)


    def test_registration_username_is_taken(self):
        url = reverse('account:registration')
        user = user_create('Test', 'srxdcfgvhkjbkn')
        data = {
            'username': 'Test',
            'password': 'qpwoeiruty',
            'password_repeat': 'qpwoeiruty',
            'email': 'test@gmail.com'
        }
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(get_user_model().objects.count(), 1)

    def test_login(self):
        user = user_create(username=self.username, password=self.password)
        url = reverse('account:login')
        data = {
            'username': self.username,
            'password': self.password
        }

        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)

        url = reverse('account:user_detail', args=(user.id, ))
        response = self.client.get(url)
        self.assertEqual(response.context['user'], user)

    def test_login_redirect_already_authenticated(self):
        user = user_create(username=self.username, password=self.password)
        is_authenticated = self.client.login(username=self.username, password=self.password)
        self.assertTrue(is_authenticated)
        url = reverse('account:login')
        data = {
            'username': self.username,
            'password': self.password
        }
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/detail.html')

    def test_login_incorrect(self):
        user = user_create(username=self.username, password=self.password)
        url = reverse('account:login')
        data = {
            'username': 'random',
            'password': 'incorrectpassword'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['user'], user)

    def test_logout(self):
        user = user_create(username=self.username, password=self.password)
        url = reverse('account:logout')
        is_authenticated = self.client.login(username=self.username, password=self.password)
        self.assertTrue(is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertNotEqual(response.context['user'], user)

    def test_logout_redirect_anonymous_user(self):
        user = user_create(username=self.username, password=self.password)
        url = reverse('account:logout')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        response = self.client.post(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateNotUsed(response, 'registration/logout.html')

   
    def test_user_detail(self):
        user = user_create(username=self.username, password=self.password)
        is_authenticated = self.client.login(username=self.username, password=self.password)
        self.assertTrue(is_authenticated)
        url = reverse('account:user_detail', args=(user.id, ))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_active)
        self.assertFalse(response.context['user'].is_staff)
        self.assertFalse(response.context['user'].is_superuser)
        self.assertIsNotNone(response.context['user'].avatar)
        self.assertEqual(response.context['user'].get_full_name(), '')
        self.assertEqual(response.context['user'].email, '')
        self.assertIsNone(response.context['user'].about_self)
        self.assertQuerySetEqual(response.context['articles'], [])
        self.assertQuerySetEqual(response.context['comments'], [])

    def test_user_edit(self):
        user = user_create(username=self.username, password=self.password)
        url = reverse('account:edit', args=(user.id, ))
        data = {
            'first_name': 'Test',
            'last_name': 'Test',
        }
        is_authenticated = self.client.login(username=self.username, password=self.password)
        self.assertTrue(is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['user'].first_name, data['first_name'])
        self.assertEqual(response.context['user'].first_name, data['first_name'])
    
    def test_user_edit_forbidden(self):
        user = user_create(username=self.username, password=self.password)
        user2 = user_create(username='123', password=self.password)
        url = reverse('account:edit', args=(user.id, ))
        data = {
            'first_name': 'Test',
            'last_name': 'Test',
            'email': 'testest@gmail.com',
        }
        is_authenticated = self.client.login(username='123', password=self.password)
        self.assertTrue(is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_email_edit(self):
        from django.core.mail import outbox
        user = user_create(username=self.username, password=self.password, email='test@test.com')
        self.client.login(username=self.username, password=self.password)
        url = reverse('account:old_email_confirmation')
        response = self.client.get(url)
        self.assertEqual(len(outbox), 1)
        old_email_conf_code = outbox[0].body[-6:]
        self.assertIsNotNone(old_email_conf_code)
        not_valid_data = {'confirmation_code': '999999'}
        response = self.client.post(url, not_valid_data)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/email_code_confirmation.html')
        data = {'confirmation_code': old_email_conf_code}
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        email_data = {'email': 'test2@gmail.com'}
        url = response.request['PATH_INFO']
        response = self.client.post(url, email_data, follow=True)
        self.assertEqual(response.status_code, 200)
        url = response.request['PATH_INFO']
        new_email_conf_code = outbox[-1].body[-6:]
        data = {'confirmation_code': new_email_conf_code}
        response = self.client.post(url, data, follow=True)
        self.assertTemplateUsed(response, 'account/detail.html')
        self.assertEqual(response.context['user'].email, email_data['email'])

    def test_email_edit_not_allowed(self):
        url = reverse('account:old_email_confirmation')
        response = self.client.get(url, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

        user = user_create(username=self.username, password=self.password, email='test@test.com')
        self.client.login(username=self.username, password=self.password)
        from django.core.mail import outbox
        response = self.client.get(url)
        self.assertEqual(len(outbox), 1)                            # Действия, чтобы получить url для account:new_email_enter
        old_email_conf_code = outbox[0].body[-6:]
        data = {'confirmation_code': old_email_conf_code}
        response = self.client.post(url, data, follow=True)
        url = response.request['PATH_INFO']

        self.client.logout()

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_password_change(self):
        user = user_create(username=self.username, password=self.password)
        url = reverse('account:password_change')
        data = {
            'old_password': self.password,
            'new_password1': 'ajfgjhsfd23dsd',
            'new_password2': 'ajfgjhsfd23dsd'
        }
        is_authenticated = self.client.login(username=self.username, password=self.password)
        self.assertTrue(is_authenticated)
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed('registration/password_change_form.html')
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/password_change_done.html')

    def test_get_secret_token_and_auth_with_it(self):
        user = user_create(username=self.username, password=self.password, email='test@test.com')
        is_authenticated = self.client.login(username=self.username, password=self.password)
        self.assertTrue(is_authenticated)
        url = reverse('account:create_authentication_token')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        password_data = {'password': self.password}
        response = self.client.post(url, password_data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'account/token_info.html')
        auth_token = response.context['authentication_token']

        # login

        self.client.logout()

        url = reverse('account:authentication_token_login')
        response = self.client.get(url)
        data = {'token': auth_token}
        self.assertEqual(response.status_code, 200)
        response = self.client.post(url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertTemplateUsed('account/detail.html')
        self.assertEqual(response.context['user'].username, self.username)