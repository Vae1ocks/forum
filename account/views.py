from django.contrib.auth import get_user_model, login
from django.db.models.query import QuerySet
from django.http import Http404, HttpResponse
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import DetailView, CreateView, TemplateView, UpdateView, FormView
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from .forms import NewEmailForm, RegistrationForm, ConfirmationCodeForm, TokenAuthenticationForm, PasswordConfirmationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.crypto import get_random_string
from django.conf import settings
from django.contrib import messages
from .tasks import confirmation_code_create
import secrets
import redis
import random


r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)


class UserDetailView(DetailView):
    model = get_user_model()
    template_name = 'account/detail.html'
    context_object_name = 'user'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.get_object()
        context['articles'] = user.articles.all()
        context['comments'] = user.comments_published.select_related('article').all()
        return context
    

class RedirectLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy('account:user_detail', kwargs={'pk': request.user.pk}))
        return super().dispatch(request, *args, **kwargs)
    
    
class RedirectLogoutView(LogoutView):
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse_lazy('account:login'))
        return super().dispatch(request, *args, **kwargs)


class RegistrationDoneView(TemplateView):
    template_name = 'registration/registration_done.html'


class UserEditView(UserPassesTestMixin, UpdateView):
    model = get_user_model()
    fields = ['avatar', 'username', 'first_name', 'last_name', 'about_self']
    template_name = 'account/edit.html'

    def test_func(self):
        user = self.get_object()
        return self.request.user == user
    
    def handle_no_permission(self):
        raise Http404()
    
    def get_success_url(self):
        return reverse_lazy('account:user_detail', kwargs={'pk': self.object.pk})
    

class RegistrationView(FormView):
    form_class = RegistrationForm
    template_name = 'registration/registration.html'
    success_url = reverse_lazy('account:registration_confirmation')

    def form_valid(self, form):
        self.request.session['registration_data'] = form.cleaned_data
        confirmation_code = random.randint(100000, 999999)
        r.set(f'user:{form.cleaned_data['username']}:confirmation_code', confirmation_code, ex=180)
        title = _('Finish the registration')
        body = _(f'Your confirmation code to complete the registration: {confirmation_code}')
        email = form.cleaned_data['email']
        confirmation_code_create(title=title, body=body, email=email)
        return super().form_valid(form)
        

class RegistrationConfirmation(FormView):
    form_class = ConfirmationCodeForm
    success_url = reverse_lazy('account:registration_done')
    template_name = 'registration/email_code_confirmation.html'

    def form_valid(self, form):
        entered_code = form.cleaned_data['confirmation_code']
        registration_data = self.request.session['registration_data']
        expected_code = r.get(f'user:{registration_data['username']}:confirmation_code')
        if registration_data:
            if entered_code == expected_code.decode('utf-8'):
                user = get_user_model().objects.create_user(
                    username=registration_data['username'],
                    first_name = registration_data['first_name'],
                    last_name = registration_data['last_name'],
                    email=registration_data['email'],
                    about_self=registration_data['about_self'],
                    avatar=registration_data['avatar'],
                    password=registration_data['password'],
                )
                return super().form_valid(form)
            return self.form_invalid(form)
        return Http404
    
    def form_invalid(self, form):
        messages.error(self.request, _('Confirmation code is not valid'))
        return super().form_invalid(form)
    

class OldEmailConfirmationView(LoginRequiredMixin, FormView):
    form_class = ConfirmationCodeForm
    template_name = 'registration/email_code_confirmation.html'

    def get_success_url(self):
        return reverse_lazy('account:new_email_enter', args=(self.redirect_token, ))

    def get(self, request, *args, **kwargs):
        confirmation_code = random.randint(100000, 999999)
        title = _('Edit your email')
        body = _(f'The confirmation code to change your email: {confirmation_code}')
        confirmation_code_create(title=title, body=body, email=request.user.email)
        r.set(f'user:{request.user.id}:old_email_conf_code', confirmation_code, ex=180)
        return super().get(request, *args, **kwargs)

    def form_valid(self, form):
        entered_code = form.cleaned_data['confirmation_code']
        expected_code = r.get(f'user:{self.request.user.id}:old_email_conf_code').decode('utf-8')

        if entered_code == expected_code:
            self.redirect_token = get_random_string(30)
            r.set(f'user:{self.request.user.id}:redirect_token', self.redirect_token, ex=20)
            r.delete(f'user:{self.request.user.id}:old_email_conf_code')
            return super().form_valid(form)
        return self.form_invalid(form)
    def form_invalid(self, form):
        messages.error(self.request, _('Confirmation code is not valid'))
        return super().form_invalid(form)
    
class NewEmailEnterView(FormView):
    form_class = NewEmailForm
    success_url = reverse_lazy('account:new_email_confirmation')
    template_name = 'registration/email_enter_form.html'

    def dispatch(self, request, *args, **kwargs):
        received_token = kwargs.get('redirect_token')
        excepted_token = r.get(f'user:{request.user.id}:redirect_token')
        if excepted_token:
            excepted_token = excepted_token.decode('utf-8')
            if excepted_token == received_token:
                return super().dispatch(request, *args, **kwargs)
            raise Http404
        raise Http404

    def form_valid(self, form):
        confirmation_code = random.randint(100000, 999999)
        r.set(f'user:{self.request.user.id}:new_email_conf_code', confirmation_code, ex=180)
        self.request.session['new_email'] = form.cleaned_data['email']
        title = _('New email confirmation')
        body = _(f'Here is your code to confirm your new email: {confirmation_code}')
        confirmation_code_create(title=title, body=body, email=form.cleaned_data['email'])
        return super().form_valid(form)
    
class NewEmailConfirmation(FormView):
    form_class = ConfirmationCodeForm
    template_name = 'registration/email_code_confirmation.html'

    def get_success_url(self):
        return reverse_lazy('account:user_detail', args=(self.request.user.id, ))
    
    def form_valid(self, form):
        expected_code = r.get(f'user:{self.request.user.id}:new_email_conf_code')
        entered_code = form.cleaned_data['confirmation_code']
        if self.request.session['new_email']:
            if expected_code.decode('utf-8') == entered_code:
                new_email = self.request.session.pop('new_email')
                self.request.user.email = new_email
                self.request.user.save()
                return super().form_valid(form)
            return self.form_invalid(form)
        return Http404

    def form_invalid(self, form):
        messages.error(self.request, _('Confirmation code is not valid'))
        return super().form_invalid(form)
    

class TokenCreateView(FormView):
    form_class = PasswordConfirmationForm
    template_name = 'account/password_confirmation.html'
    success_url = reverse_lazy('account:authentication_token_info')
    
    def form_valid(self, form):
        is_token_already_exist = r.get(f'user:{self.request.user.id}:authentication_token')

        if is_token_already_exist is not None:
            authentication_token = is_token_already_exist.decode('utf-8')
            r.delete(f'user:{self.request.user.id}:authentication_token')
            r.delete(f'auth_token:{authentication_token}:user')

        if self.request.user.check_password(form.cleaned_data['password']):
            random_quantity = random.randint(50, 70)
            authentication_token = secrets.token_urlsafe(random_quantity)
            r.set(f'user:{self.request.user.id}:authentication_token', authentication_token, 360000)
            r.set(f'auth_token:{authentication_token}:user', self.request.user.username, ex=360000)
            messages.success(self.request, _('New authentication token has been created'))
            return super().form_valid(form)
        return self.form_invalid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, _('Password incorrect'))
        return super().form_invalid(form)
        

class TokenInfoView(TemplateView):
    template_name = 'account/token_info.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        authentication_token = r.get(f'user:{self.request.user.id}:authentication_token').decode('utf-8')
        context['authentication_token'] = authentication_token
        return context


class TokenLoginView(FormView):
    form_class = TokenAuthenticationForm
    template_name = 'registration/token_login.html'

    def get_success_url(self):
        return reverse_lazy('account:user_detail', kwargs={'pk': self.request.user.pk})
    
    def form_valid(self, form):
        entered_token = form.cleaned_data['token']
        username = r.get(f'auth_token:{entered_token}:user')
        if username is not None:
            username = username.decode('utf-8')
            try:
                user = get_user_model().objects.get(username=username)
                login(self.request, user, backend='django.contrib.auth.backends.ModelBackend')
                return super().form_valid(form)
            except get_user_model().DoesNotExist: raise Http404
        return Http404