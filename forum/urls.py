from django.contrib import admin
from django.urls import path, include
from django.contrib.sitemaps.views import sitemap
from blog.sitemaps import ArticleSitemap
from account.sitemaps import UserSitemap
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns


sitemaps = {
    'articles': ArticleSitemap,
    'users': UserSitemap
}

urlpatterns = i18n_patterns(
    path('admin/', admin.site.urls),
    path('account/', include('account.urls', namespace='account')),
    path('blog/', include('blog.urls', namespace='blog')),
    path('rosetta/', include('rosetta.urls')),
    path('social-auth/', include('social_django.urls', namespace='social')),
    path('api/', include('api.urls', namespace='api')),
    path('api-auth/', include('rest_framework.urls')),
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps},
         name='sitemap'),
)

if settings.DEBUG:
    # '''
    import debug_toolbar
    urlpatterns += path("__debug__/", include("debug_toolbar.urls")),
    # '''
    urlpatterns += static(settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT)