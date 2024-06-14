from django.contrib.sitemaps import Sitemap
from django.contrib.auth import get_user_model
from django.urls import reverse


class UserSitemap(Sitemap):
    changefreq = 'never'
    priority = 0.4

    def items(self):
        return get_user_model().objects.all()
    
    def lastmod(self, obj):
        return obj.user_updated

    def location(self, obj):
        return reverse('account:user_detail', args=(obj.pk, ))