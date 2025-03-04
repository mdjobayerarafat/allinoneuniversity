from django.contrib import admin
from .models import Cafeteria, MenuItem, DailyMenu, Order, OrderItem, OrderStatusUpdate

@admin.register(Cafeteria)
class CafeteriaAdmin(admin.ModelAdmin):
    list_display = ('name', 'location', 'owner', 'opening_time', 'closing_time')
    list_filter = ('owner',)
    search_fields = ('name', 'location')
    raw_id_fields = ('owner',)


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'cafeteria', 'category', 'price', 'availability')
    list_filter = ('cafeteria', 'category', 'availability')
    search_fields = ('name', 'description')
    list_editable = ('price', 'availability')


class MenuItemInline(admin.TabularInline):
    model = DailyMenu.items.through
    extra = 1


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ('cafeteria', 'date', 'created_by', 'created_at')
    list_filter = ('cafeteria', 'date')
    search_fields = ('cafeteria__name',)
    raw_id_fields = ('created_by',)
    date_hierarchy = 'date'
    inlines = [MenuItemInline]
    exclude = ('items',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1
    readonly_fields = ('price',)


class OrderStatusUpdateInline(admin.TabularInline):
    model = OrderStatusUpdate
    extra = 0
    readonly_fields = ('timestamp',)
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'cafeteria', 'status', 'total_price', 'created_at', 'pickup_time')
    list_filter = ('status', 'cafeteria', 'delivery_option')
    search_fields = ('user__username', 'user__email', 'cafeteria__name')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user', 'cafeteria', 'completed_by')
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline, OrderStatusUpdateInline]

    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'cafeteria', 'status', 'pickup_time', 'delivery_option')
        }),
        ('Order Details', {
            'fields': ('total_price', 'notes')
        }),
        ('Completion Information', {
            'fields': ('completed_by', 'completed_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'menu_item', 'quantity', 'price')
    list_filter = ('order__status',)
    search_fields = ('order__id', 'menu_item__name')
    raw_id_fields = ('order', 'menu_item')


@admin.register(OrderStatusUpdate)
class OrderStatusUpdateAdmin(admin.ModelAdmin):
    list_display = ('order', 'status', 'timestamp', 'updated_by')
    list_filter = ('status',)
    search_fields = ('order__id', 'notes')
    raw_id_fields = ('order', 'updated_by')
    readonly_fields = ('timestamp',)