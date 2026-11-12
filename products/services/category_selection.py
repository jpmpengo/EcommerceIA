from django.db.models import Q


def refine_selection(selected_ids, category):
    selected = set(selected_ids)
    ancestors = []
    parent = category.parent
    while parent is not None:
        ancestors.append(parent.id)
        parent = parent.parent
    selected.difference_update(ancestors)
    from products.models import Category
    descendants = Category.objects.filter(Q(parent=category) | Q(parent__parent=category)).values_list("id", flat=True)
    selected.difference_update(descendants)
    selected.add(category.id)
    return sorted(selected)


def category_union_filter(categories):
    result = Q(pk__in=[])
    for category in categories:
        result |= Q(category=category) | Q(category__parent=category) | Q(category__parent__parent=category)
    return result
