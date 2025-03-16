from django.db.models import Count, Sum
from django.db.models.functions import ExtractYear, ExtractMonth
from django.shortcuts import render
from django.utils import timezone

from customers.models import Customer, Order, OrderStatuses

MONTHS_NAMES = {
    "1": "Январь",
    "2": "Февраль",
    "3": "Март",
    "4": "Апрель",
    "5": "Май",
    "6": "Июнь",
    "7": "Июль",
    "8": "Август",
    "9": "Сентябрь",
    "10": "Октябрь",
    "11": "Ноябрь",
    "12": "Декабрь"
}


def get_readable_month_and_year(annotated_booking):
    return f'{MONTHS_NAMES.get(str(annotated_booking["month"]))} {annotated_booking["year"]}'


def dashboard_view(request):
    period = request.GET.get('period')  # today/last_week/last_month/last_year
    group_by_field = 'created_at__date'
    if period == 'today':
        filter_period = timezone.now().date()
    elif period == 'last_week':
        filter_period = timezone.now() - timezone.timedelta(days=7)
    elif period == 'last_year':
        group_by_field = 'month_year'
        filter_period = timezone.now() - timezone.timedelta(days=365)
    else:
        period = 'last_month'
        filter_period = timezone.now() - timezone.timedelta(days=30)

    users_total = Customer.objects.filter(created_at__gte=filter_period)
    users_count_total = users_total.count()
    orders_total = Order.objects.filter(status=OrderStatuses.DELIVERED, created_at__gte=filter_period)
    orders_count_total = orders_total.count()
    if period == 'last_year':
        users_dates = (
            users_total
            .annotate(year=ExtractYear('created_at'), month=ExtractMonth('created_at'))
            .values('year', 'month')
            .annotate(users_count=Count('id'))
            .order_by('year', 'month')
        )
        orders_dates = (
            orders_total
            .annotate(year=ExtractYear('created_at'), month=ExtractMonth('created_at'))
            .values('year', 'month')
            .annotate(orders_count=Count('id'))
            .order_by('year', 'month')
        )
    else:
        users_dates = users_total.values(group_by_field).annotate(users_count=Count('id')).order_by(group_by_field)
        orders_dates = orders_total.values(group_by_field).annotate(orders_count=Count('id')).order_by(group_by_field)
    users_dates_list = []
    users_count_list = []
    for item in users_dates:
        users_dates_list.append(get_readable_month_and_year(item) if period == "last_year" else item[group_by_field])
        users_count_list.append(item['users_count'])
    orders_dates_list = []
    orders_count_list = []
    for item in orders_dates:
        orders_dates_list.append(get_readable_month_and_year(item) if period == "last_year" else item[group_by_field])
        orders_count_list.append(item['orders_count'])
    successful_revenue_amount = orders_total.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    return render(request, "dashboard.html", {
        "period": period,
        "users_count_total": users_count_total,
        "users_dates_list": users_dates_list,
        "users_count_list": users_count_list,
        "orders_count_total": orders_count_total,
        "orders_dates_list": orders_dates_list,
        "orders_count_list": orders_count_list,
        "successful_revenue_amount": successful_revenue_amount,
    })
