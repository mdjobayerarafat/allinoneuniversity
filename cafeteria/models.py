from django.db import models
from django.utils import timezone

class Cafeteria(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    opening_time = models.TimeField()
    closing_time = models.TimeField()
    owner = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='owned_cafeterias',
        help_text="User who can manage this cafeteria's menus and orders"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Cafeterias"


class MenuItem(models.Model):
    cafeteria = models.ForeignKey(Cafeteria, on_delete=models.CASCADE, related_name='menu_items')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    category = models.CharField(max_length=50)  # e.g., Breakfast, Lunch, Dinner, Snack
    availability = models.BooleanField(default=True)
    image = models.ImageField(upload_to='menu_items/', blank=True, null=True)
    nutritional_info = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"{self.name} (${self.price})"


class DailyMenu(models.Model):
    cafeteria = models.ForeignKey(Cafeteria, on_delete=models.CASCADE, related_name='daily_menus')
    date = models.DateField()
    items = models.ManyToManyField(MenuItem, related_name='daily_menus')
    created_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_menus'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('cafeteria', 'date')
        verbose_name_plural = "Daily Menus"

    def __str__(self):
        return f"{self.cafeteria.name} - {self.date}"


class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready for Pickup'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    )
    DELIVERY_CHOICES = (
        ('pickup', 'Pickup'),
        ('dine_in', 'Dine In'),
    )
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    cafeteria = models.ForeignKey(
        Cafeteria,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    pickup_time = models.DateTimeField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    delivery_option = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='pickup')
    notes = models.TextField(blank=True)
    total_price = models.DecimalField(max_digits=8, decimal_places=2)
    completed_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_orders'
    )
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Order #{self.id} - {self.status}"

    def complete_order(self, completed_by):
        """Mark order as completed by cafeteria owner/staff"""
        self.status = 'completed'
        self.completed_by = completed_by
        self.completed_at = timezone.now()
        self.save()

        # Create status update record
        OrderStatusUpdate.objects.create(
            order=self,
            status='completed',
            notes=f"Order completed by {completed_by.username}"
        )

    def update_status(self, new_status, notes="", user=None):
        """Update order status and create status history entry"""
        if new_status in dict(self.STATUS_CHOICES).keys():
            old_status = self.status
            self.status = new_status

            if new_status == 'completed' and user:
                self.completed_by = user
                self.completed_at = timezone.now()

            self.save()

            # Create status update record
            OrderStatusUpdate.objects.create(
                order=self,
                status=new_status,
                notes=notes,
                updated_by=user
            )
            return True
        return False


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    menu_item = models.ForeignKey(MenuItem, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    special_instructions = models.TextField(blank=True)

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    def save(self, *args, **kwargs):
        # Set the price based on menu item if not already set
        if not self.price:
            self.price = self.menu_item.price * self.quantity
        super().save(*args, **kwargs)


class OrderStatusUpdate(models.Model):
    """Track history of order status changes"""
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='status_history'
    )
    status = models.CharField(max_length=20, choices=Order.STATUS_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    updated_by = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='status_updates'
    )

    def __str__(self):
        return f"Order #{self.order.id}: {self.get_status_display()}"

    class Meta:
        ordering = ['-timestamp']