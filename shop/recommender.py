import redis
from django.conf import settings
from .models import Product


# connect to redis
#r = redis.StrictRedis(host=settings.REDIS_HOST, port=settings.REDIS_PORT, db=settings.REDIS_DB)

# connect to redislite
r = settings.RDB

class Recommender(object):

    def get_product_key(self, id):
        return 'product:{}:purchased_with'.format(id)

    def products_bought(self, products):
        # создаем список идентификаторов продуктов
        product_ids = [p.id for p in products]
        for product_id in product_ids:
            for with_id in product_ids:
                # get the other products bought with each product
                # получить другие продукты, купленные с каждым из этих продуктов
                if product_id != with_id:
                    # increment score for product purchased together
                    # увеличиваем на 1 счетчик продукта, купленного вместе с этим
                    r.zincrby(self.get_product_key(product_id), amount=1, value=with_id)

    def suggest_products_for(self, products, max_results=6):
        # создаем список идентификаторов продуктов
        product_ids = [p.id for p in products]
        if len(products) == 1:
            # only 1 product
            # если выбран только 1 продукт
            suggestions = r.zrange(self.get_product_key(product_ids[0]), 0, -1, desc=True)[:max_results]
        else:
            # generate a temporary key
            # генерируем временный ключ
            flat_ids = ''.join([str(id) for id in product_ids])
            tmp_key = 'tmp_{}'.format(flat_ids)
            # multiple products, combine scores of all products
            # store the resulting sorted set in a temporary key
            # если продуктов несколько, объединяем оценки всех продуктов
            # сохраняем полученный отсортированный набор во временном ключе
            keys = [self.get_product_key(id) for id in product_ids]
            r.zunionstore(tmp_key, keys)
            # remove ids for the products the recommendation is for
            # удаляем идентификаторы для рекомендуемых продуктов
            r.zrem(tmp_key, *product_ids)
            # get the product ids by their score, descendant sort
            # получаем идентификаторы продуктов отсортированные по убыванию их счетчика
            suggestions = r.zrange(tmp_key, 0, -1, desc=True)[:max_results]
            # remove the temporary key
            # удаляем временный ключ
            r.delete(tmp_key)
        suggested_products_ids = [int(id) for id in suggestions]
        # get suggested products and sort by order of appearance
        # предлагаем продукты отсортированные по порядку появления
        suggested_products = list(Product.objects.filter(id__in=suggested_products_ids))
        suggested_products.sort(key=lambda x: suggested_products_ids.index(x.id))
        return suggested_products

    def clear_purchases(self):
        for id in Product.objects.values_list('id', flat=True):
            r.delete(self.get_product_key(id))


