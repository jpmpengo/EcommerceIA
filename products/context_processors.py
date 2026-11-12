from .models import Category


def categories(request):
    return {
        "menu_categories": Category.objects.filter(parent__isnull=True).prefetch_related('children').order_by('name'),
    }