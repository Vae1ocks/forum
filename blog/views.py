from django.shortcuts import redirect, render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, UpdateView, FormView, CreateView, DeleteView
from .models import Article, Comment
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .forms import CommentForm, SearchForm, TagSelectionForm
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.db.models import Count
from django.contrib.postgres.search import TrigramSimilarity
from django.utils.text import slugify
from django.http import Http404
from taggit.models import Tag
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from unidecode import unidecode
from django.contrib import messages
from django.core.cache import cache
import redis


r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)


class ArticleListView(ListView):
    model = Article
    paginate_by = 5
    template_name = 'blog/article/list.html'
    context_object_name = 'articles'

    def get_queryset(self):
        queryset = cache.get('queryset')
        if not queryset:
            queryset = Article.published.all().select_related('author').prefetch_related('tags')
            tag_get_arg = self.request.GET.get('tag')
            tag_kwarg = self.kwargs.get('tag')
            if tag_get_arg:
                queryset = queryset.filter(tags__slug=tag_get_arg)
            elif tag_kwarg:
                queryset = queryset.filter(tags__slug=tag_kwarg)
                cache.set('queryset', queryset)
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_articles'] = Article.published.count()
        context['all_tags'] = Tag.objects.all()
        return context


class ArticleDetailView(DetailView):
    model = Article
    template_name = 'blog/article/article_detail.html'
    context_object_name = 'article'

    def get_queryset(self):
        queryset = Article.objects.all().select_related('author')
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if context['article'].status == Article.Status.DRAFT and self.request.user != context['article'].author:
            raise Http404
        articles_with_same_tags = cache.get(f'article:{context['article'].id}:same_articles')
        if not articles_with_same_tags:
            tags_ids = context['article'].tags.values_list('id', flat=True)
            articles_with_same_tags = Article.published.filter(tags__in=tags_ids).exclude(id=context['article'].id)
            articles_with_same_tags = articles_with_same_tags.annotate(same_tags=Count('tags'))\
                                                        .order_by('-same_tags', '-publish')[:5]
            cache.set(f'article:{context['article'].id}:same_articles', articles_with_same_tags)
        context['comments'] = Comment.objects.filter(article=context['article']).prefetch_related('author')
        context['articles_with_same_tags'] = articles_with_same_tags
        context['form'] = CommentForm
        article_id = context['article'].id
        user_id = self.request.user.id if self.request.user.is_authenticated else None
        if user_id:
            user_key = f'user:{user_id}:viewed_articles'
            if not r.sismember(user_key, article_id):
                r.incr(f'article:{article_id}:views')
                r.sadd(user_key, article_id)
        else:
            session_key = f'viewed_article_{article_id}'
            if not self.request.session.get(session_key, False):
                r.incr(f'article:{article_id}:views')
                self.request.session[session_key] = True
        views = r.get(f'article:{article_id}:views')
        context['all_views'] = int(views)
        return context

@login_required
@require_POST
def comment_create(request, id):
    article = get_object_or_404(Article,
                             id=id,
                             status=Article.Status.PUBLISHED)
    comment = None
    form = CommentForm(data=request.POST)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.article = article
        comment.author = request.user
        comment.save()
    return redirect(reverse_lazy('blog:article_detail', args=(article.slug, article.id)))


class ArticleSearchView(FormView):
    template_name = 'blog/article/search.html'
    form_class = SearchForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = self.request.GET.get('query')
        results = cache.get(query)
        if not results:
            if query:
                results = Article.published.annotate(similarity=TrigramSimilarity('title', query),
                                                    ).filter(similarity__gt=0.1).order_by('-similarity')
            else:
                results = []
            cache.set(query, results)
        context['results'] = results
        context['query'] = query
        return context
    

class ArticleCreateView(LoginRequiredMixin, CreateView):
    model = Article
    fields = ['title', 'body', 'status']
    template_name = 'blog/article/article_create.html'
    success_url = reverse_lazy('blog:article_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['all_tags'] = Tag.objects.values_list('name', flat=True)
        context['tag_form'] = TagSelectionForm
        return context

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.slug = slugify(unidecode(form.instance.title))
        tags = self.request.POST.getlist('tags') 
        if tags:
            response = super().form_valid(form)
            for id in tags:
                tag = Tag.objects.get(id=id)
                form.instance.tags.add(tag)
            if form.instance.status == 'PB':
                messages.success(self.request, _('Your article has been successfully created.\
                                                 It will be shown in the list of articles within 15 minutes '))
            else:
                messages.success(self.request, _('Your article has been created with draft status.\
                                                 Only you can see this'))
            return response
        return self.form_invalid(form, tags)
    
    def form_invalid(self, form, tags):
        if not tags:
            messages.error(self.request, _('You must choose at least 1 tag'))
        return super().form_invalid(form)


class ArticleEditView(UserPassesTestMixin, UpdateView):
    model = Article
    fields = ['title', 'body', 'status']
    template_name = 'blog/article/article_edit.html'

    def test_func(self):
        article = self.get_object()
        return self.request.user == article.author
    
    def handle_no_permission(self):
        raise Http404
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag_form'] = TagSelectionForm(
            initial={'tags': self.object.tags.values_list('id', flat=True)}
        )
        return context
    
    def form_valid(self, form):
        tags = self.request.POST.getlist('tags')
        if tags:
            for id in tags:
                try:
                    tag = Tag.objects.get(id=id)
                    form.instance.tags.add(tag)
                except Tag.DoesNotExist:
                    pass
            if form.instance.status == 'PB':
                messages.success(self.request, _('Your article has been updated.\
                                You will see changes within 15 minutes.'))
            else:
                messages.success(self.request, 'Your article has been updated.\
                                 Only you can see this article.')
            return super().form_valid(form)
        return self.form_invalid(form, tags)
    
    def form_invalid(self, form, tags):
        if not tags:
            messages.error(self.request, _('You must choose at least 1 tag'))
        return super().form_invalid(form)


class ArticleDeleteView(UserPassesTestMixin, DeleteView):
    model = Article
    success_url = reverse_lazy('blog:article_list')
    template_name = 'blog/article/article_delete.html'
    
    def test_func(self):
        article = self.get_object()
        return self.request.user == article.author
    
    def handle_no_permission(self):
        raise Http404

class CommentEditView(UserPassesTestMixin, UpdateView):
    model = Comment
    fields = ['body']

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author
    
    def handle_no_permission(self):
        raise Http404
    

class CommentDeleteView(UserPassesTestMixin, DeleteView):
    model = Comment
    template_name = 'blog/article/comment_delete.html'
    pk_url_kwarg = 'comment_id'

    def get_success_url(self):
        comment = self.get_object()
        article = comment.article
        return reverse_lazy('blog:article_detail', args=(article.slug, article.id ))

    def test_func(self):
        comment = self.get_object()
        return self.request.user == comment.author
    
    def handle_no_permission(self):
        raise Http404
    
    def form_valid(self, form):
        messages.success(self.request, _('Your comment has been deleted'))
        return super().form_valid(form)