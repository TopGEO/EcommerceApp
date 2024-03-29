from category.models import Category
def menu_links(request):
    return dict(categories=Category.objects.all())
