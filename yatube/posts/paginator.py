from django.core.paginator import Paginator

from yatube.settings import PAGINATOR_COUNT


def paginator_page(request, queryset):
    return Paginator(
        queryset, PAGINATOR_COUNT).get_page(request.GET.get('page'))
