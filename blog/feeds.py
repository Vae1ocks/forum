import markdown
from django.contrib.syndication.views import Feed 
from django.template.defaultfilters import truncatewords_html 
from django.urls import reverse_lazy
from .models import Article


class LatestArticlesFeed(Feed):
    title = 'Forum'
    link = reverse_lazy('blog:article_list')
    description = 'Recent topics and publications'

    def items(self):
        return Article.published.all()[:5]
    
    def item_title(self, item):
        return item.title 
    
    def item_description(self, item):
        return truncatewords_html(markdown.markdown(item.body), 25)
    
    def item_publishdate(self, item):
        return item.publish
