from django.shortcuts import render, get_object_or_404
from .models import Category, Product
from cart.forms import CartAddProductForm
from .recommender import Recommender
from django.http import HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import CommentForm

 
def product_list(request, category_slug=None):
    category = None
    categories = Category.objects.all()
    products = Product.objects.filter(available=True)
    if category_slug:
        #category = get_object_or_404(Category, slug=category_slug)
        language = request.LANGUAGE_CODE
        category = get_object_or_404(Category, translations__language_code=language, translations__slug=category_slug)
        products = products.filter(category=category)
    paginator = Paginator(products, 6)
    page = request.GET.get('page')
    try:
        products = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer deliver the first page
        products = paginator.page(1)
    except EmptyPage:
        if request.is_ajax():
            # If the request is AJAX and the page is out of range
            # return an empty page
            return HttpResponse('')
        # If page is out of range deliver last page of results
        products = paginator.page(paginator.num_pages)
    if request.is_ajax():
        return render(request, 'shop/product/list_ajax.html', 
                   {'section': 'products', 
                    'category': category, 
                    'categories': categories, 
                    'products': products})
    return render(request, 'shop/product/list.html', 
                {'section': 'products', 
                 'category': category, 
                 'categories': categories, 
                 'products': products})


def product_detail(request, id, slug):
    #product = get_object_or_404(Product, id=id, slug=slug, available=True)
    language = request.LANGUAGE_CODE
    product = get_object_or_404(Product, id=id, translations__language_code=language, translations__slug=slug, available=True)
    cart_product_form = CartAddProductForm()
    r = Recommender()
    recommended_products = r.suggest_products_for([product], 4)
    # Список активных комментариев к этому продукту
    comments = product.comments.filter(active=True)
    new_comment = None
    if (request.method == 'POST') and request.user.is_authenticated:
        # Комментарий отправлен
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            # Создать объект комментариев, но еще не сохранять его в базе данных 
            new_comment = comment_form.save(commit=False)
            # Связать текущий товар с комментарием
            new_comment.product = product
            new_comment.user = request.user
            new_comment.name = request.user.first_name
            new_comment.id_user = request.user.id
            # Сохранить комментарий в базе данных
            new_comment.save()
    else:
        comment_form = CommentForm()
    return render(request, 'shop/product/detail.html', 
                   {'product': product, 
                    'cart_product_form': cart_product_form, 
                    'comments': comments,
                    'new_comment': new_comment,
                    'comment_form': comment_form,
                    'recommended_products': recommended_products
                    })
    """
    return render(request, 
                'shop/product/detail.html',
                {'product': product,
                'cart_product_form': cart_product_form,
                'recommended_products': recommended_products})
    """
