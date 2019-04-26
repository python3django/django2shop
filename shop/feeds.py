from django.contrib.syndication.views import Feed
from django.template.defaultfilters import truncatewords
from .models import Product
#from django.utils.translation import gettext_lazy as _


class LatestProductFeed(Feed):
    title = 'Мой магазин'
    link = '/'
    description = 'Новые продукты в моем магазине.'

    def items(self):
        return Product.objects.all()[:5]

    def item_title(self, item):
        return item.name

    def item_description(self, item):
        return truncatewords(item.description, 30)

