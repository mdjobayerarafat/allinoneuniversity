from django import forms
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.db.models import Sum, F, ExpressionWrapper, DecimalField

from .models import Cafeteria, MenuItem, DailyMenu, Order, OrderItem


class DateInput(forms.DateInput):
    input_type = 'date'


class TimeInput(forms.TimeInput):
    input_type = 'time'


class DateTimeInput(forms.DateTimeInput):
    input_type = 'datetime-local'


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['cafeteria', 'name', 'description', 'price', 'category', 'availability', 'image', 'nutritional_info']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nutritional_info'].widget = forms.Textarea(attrs={'rows': 3})
        self.fields['nutritional_info'].help_text = 'Enter as JSON: {"calories": 250, "protein": "10g", "fat": "5g"}'


class DailyMenuForm(forms.ModelForm):
    class Meta:
        model = DailyMenu
        fields = ['cafeteria', 'date', 'items']
        widgets = {
            'date': DateInput(),
            'items': forms.CheckboxSelectMultiple(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['items'].queryset = MenuItem.objects.filter(availability=True)

        # If cafeteria is already set, filter items by that cafeteria
        instance = kwargs.get('instance')
        if instance and instance.cafeteria:
            self.fields['items'].queryset = self.fields['items'].queryset.filter(cafeteria=instance.cafeteria)

        # If this is a POST request and cafeteria is selected, filter by that
        if args and 'cafeteria' in args[0]:
            try:
                cafeteria_id = int(args[0]['cafeteria'])
                self.fields['items'].queryset = self.fields['items'].queryset.filter(cafeteria_id=cafeteria_id)
            except (ValueError, KeyError):
                pass


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['cafeteria', 'pickup_time']
        widgets = {
            'pickup_time': DateTimeInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Set minimum pickup time to 15 minutes from now
        min_pickup_time = timezone.now() + timezone.timedelta(minutes=15)
        self.fields['pickup_time'].widget.attrs['min'] = min_pickup_time.strftime('%Y-%m-%dT%H:%M')

        # For existing orders, don't allow changing the cafeteria
        instance = kwargs.get('instance')
        if instance:
            self.fields['cafeteria'].disabled = True

    def clean_pickup_time(self):
        pickup_time = self.cleaned_data.get('pickup_time')
        cafeteria = self.cleaned_data.get('cafeteria')
        now = timezone.now()

        # Check if pickup time is at least 15 minutes from now
        if pickup_time and (pickup_time - now).total_seconds() < 900:  # 900 seconds = 15 minutes
            raise ValidationError('Pickup time must be at least 15 minutes from now.')

        # Check if the cafeteria is open at the pickup time
        if pickup_time and cafeteria:
            pickup_time_only = pickup_time.time()
            if pickup_time_only < cafeteria.opening_time or pickup_time_only > cafeteria.closing_time:
                raise ValidationError(
                    f'The cafeteria is only open from {cafeteria.opening_time} to {cafeteria.closing_time}.')

        return pickup_time


class OrderItemForm(forms.ModelForm):
    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'special_instructions']
        widgets = {
            'special_instructions': forms.Textarea(attrs={'rows': 2, 'placeholder': 'Any special requests?'}),
        }


class OrderItemFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        # Check if at least one item is ordered
        if not any(form.cleaned_data and not form.cleaned_data.get('DELETE', False)
                   for form in self.forms):
            raise ValidationError('You must order at least one item.')

        # Calculate total price for the order
        total_price = 0
        for form in self.forms:
            if form.cleaned_data and not form.cleaned_data.get('DELETE', False):
                menu_item = form.cleaned_data.get('menu_item')
                quantity = form.cleaned_data.get('quantity')
                if menu_item and quantity:
                    total_price += menu_item.price * quantity

        # Store total price to use in the view
        self.instance.total_price = total_price


class CafeteriaFilterForm(forms.Form):
    location = forms.CharField(required=False, label='Location',
                               widget=forms.TextInput(attrs={'placeholder': 'Search by location'}))

    open_now = forms.BooleanField(required=False, label='Open Now')

    def filter_queryset(self, queryset):
        location = self.cleaned_data.get('location')
        open_now = self.cleaned_data.get('open_now')

        if location:
            queryset = queryset.filter(location__icontains=location)

        if open_now:
            now = timezone.now().time()
            queryset = queryset.filter(opening_time__lte=now, closing_time__gte=now)

        return queryset


class MenuItemFilterForm(forms.Form):
    CATEGORY_CHOICES = [
        ('', 'All Categories'),
        ('Breakfast', 'Breakfast'),
        ('Lunch', 'Lunch'),
        ('Dinner', 'Dinner'),
        ('Snack', 'Snack'),
        ('Beverage', 'Beverage'),
    ]

    search = forms.CharField(required=False, label='Search',
                             widget=forms.TextInput(attrs={'placeholder': 'Search menu items'}))
    category = forms.ChoiceField(choices=CATEGORY_CHOICES, required=False)
    cafeteria = forms.ModelChoiceField(queryset=Cafeteria.objects.all(), required=False, empty_label='All Cafeterias')

    min_price = forms.DecimalField(required=False, min_value=0, decimal_places=2, label='Min Price')
    max_price = forms.DecimalField(required=False, min_value=0, decimal_places=2, label='Max Price')

    def filter_queryset(self, queryset):
        search = self.cleaned_data.get('search')
        category = self.cleaned_data.get('category')
        cafeteria = self.cleaned_data.get('cafeteria')
        min_price = self.cleaned_data.get('min_price')
        max_price = self.cleaned_data.get('max_price')

        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

        if category:
            queryset = queryset.filter(category=category)

        if cafeteria:
            queryset = queryset.filter(cafeteria=cafeteria)

        if min_price is not None:
            queryset = queryset.filter(price__gte=min_price)

        if max_price is not None:
            queryset = queryset.filter(price__lte=max_price)

        return queryset


class OrderFilterForm(forms.Form):
    STATUS_CHOICES = [
                         ('', 'All Statuses'),
                     ] + list(Order.STATUS_CHOICES)

    status = forms.ChoiceField(choices=STATUS_CHOICES, required=False)
    cafeteria = forms.ModelChoiceField(queryset=Cafeteria.objects.all(), required=False, empty_label='All Cafeterias')
    date_from = forms.DateField(required=False, widget=DateInput(), label='From Date')
    date_to = forms.DateField(required=False, widget=DateInput(), label='To Date')

    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')

        if date_from and date_to and date_from > date_to:
            raise ValidationError('From date must be before to date.')

        return cleaned_data

    def filter_queryset(self, queryset):
        status = self.cleaned_data.get('status')
        cafeteria = self.cleaned_data.get('cafeteria')
        date_from = self.cleaned_data.get('date_from')
        date_to = self.cleaned_data.get('date_to')

        if status:
            queryset = queryset.filter(status=status)

        if cafeteria:
            queryset = queryset.filter(cafeteria=cafeteria)

        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)

        return queryset