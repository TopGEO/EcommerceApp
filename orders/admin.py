from django.contrib import admin

from orders.models import Order, Payment, OrderProduct

class OrderProductInline(admin.TabularInline):
    model = OrderProduct
    extra = 0
    readonly_fields = ('payment', 'user', 'product', 'product_price', 'quantity', 'ordered',)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'full_name', 'email', 'phone', 'city', 'order_total', 'tax', 'status', 'created_at', 'is_ordered']
    list_filter = ['status', 'is_ordered']
    search_fields = ['order_number', 'first_name', 'last_name', 'email', 'phone']
    list_per_page = 20
    inlines = [OrderProductInline]

# Register your models here.
admin.site.register(Order, OrderAdmin)
admin.site.register(Payment)
admin.site.register(OrderProduct)