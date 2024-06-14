from django.contrib.sitemaps import Sitemap
from .models import Article 
from django.urls import reverse
import redis
from django.conf import settings

r = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    db=settings.REDIS_DB,
)

class ArticleSitemap(Sitemap):
    changefreq = 'never'

    def items(self):
        return Article.published.all()
    
    def lastmod(self, obj):
        return obj.updated
    
    def location(self, obj):
        return reverse('blog:article_detail', args=(obj.slug, obj.id))
    
    def priority(self, obj):
        views = r.get(f'article:{obj.id}:views')
        if views is not None:
            if int(views) >= 300:
                return 0.8
            elif int(views) >= 100:
                return 0.7
        else:
            return 0.5