from django.http import Http404
from django.shortcuts import render, get_object_or_404
from category.models import Category
from store.models import Product


# Create your views here.
def store(request, category_slug=None):
    categories = None
    products = None
    if category_slug != None:
        categories = get_object_or_404(Category, category_slug=category_slug)
        products = Product.objects.filter(category=categories, is_available=True)
        products_count = products.count()
    else:
        products = Product.objects.all().filter(is_available=True)
        products_count = products.count()

    context = {
        'products': products,
        'count': products_count,
    }
    return render(request, 'store/store.html',context)

def product_detail(request,category_slug, product_slug):
    try:
        single_product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Product.DoesNotExist:
        raise Http404("Product does not exist")
    context = {
        'single_product': single_product,
    }
    return render(request, 'store/product_detail.html', context)