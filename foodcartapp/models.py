from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import F, Sum, Count, Case, When, Value
from phonenumber_field.modelfields import PhoneNumberField

from utils.yandex_geo import fetch_coordinates


class Geo(models.Model):
    lat = models.DecimalField(
        'широта',
        max_digits=9,
        decimal_places=6,
    )
    lon = models.DecimalField(
        'долгота',
        max_digits=9,
        decimal_places=6,
    )

    created_at = models.DateTimeField(
        'время фиксации',
        auto_now=True,
        db_index=True,
    )

    class Meta:
        verbose_name = 'геопозиция'
        verbose_name_plural = 'геопозиции'

    def __str__(self):
        return f'{self.lat} {self.lon} от {self.created_at}'


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )
    coordinates = models.ForeignKey(
        Geo,
        verbose_name='геопозиция',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
            .filter(availability=True)
            .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'пункт меню ресторана'
        verbose_name_plural = 'пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


class OrderQuerySet(models.QuerySet):
    def with_total_price(self):
        return self.annotate(
            total_price=Sum(
                F('order_list__quantity') * F('order_list__price')
            )
        )

    def with_status_by(self):
        status_order = Case(
            *[
                When(
                    status=status[0], then=Value(k)
                ) for k, status in enumerate(Order.STATUSES)
            ]
        )
        return self.annotate(status_by=status_order).order_by('status_by')


class Order(models.Model):
    STATUSES = (
        ('Unprocessed', 'Необработан'),
        ('Cooking', 'Готовится'),
        ('Delivering', 'Доставляется'),
        ('Completed', 'Завершён'),
    )
    PAYMENT_TYPES = (
        ('Digital', 'Электронно'),
        ('Cash', 'Наличностью')
    )
    first_name = models.CharField(
        'имя',
        max_length=255,
    )
    last_name = models.CharField(
        'фамилия',
        max_length=255,
    )
    address = models.CharField(
        'адрес',
        max_length=255,
        db_index=True
    )
    status = models.CharField(
        'статус',
        max_length=12,
        choices=STATUSES,
        default=STATUSES[0][0],
        db_index=True
    )
    payment_type = models.CharField(
        'способ оплаты',
        max_length=12,
        choices=PAYMENT_TYPES,
        default=PAYMENT_TYPES[0][0],
        db_index=True
    )
    comment = models.TextField(
        'комментарий',
        blank=True
    )
    registered_at = models.DateTimeField(
        'Время регистрации',
        auto_now_add=True,
        db_index=True,
    )
    called_at = models.DateTimeField(
        'Время звонка',
        null=True,
        blank=True,
        db_index=True
    )
    completed_at = models.DateTimeField(
        'Время завершения',
        null=True,
        blank=True,
        db_index=True
    )
    phone_number = PhoneNumberField(
        verbose_name='номер телефона'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='ресторан',
        on_delete=models.SET_NULL,
        related_name='orders',
        null=True,
        blank=True
    )
    coordinates = models.ForeignKey(
        Geo,
        verbose_name='геопозиция',
        on_delete=models.SET_NULL,
        blank=True,
        null=True
    )
    objects = OrderQuerySet.as_manager()

    def get_restaurants(self):
        required_products = self.order_list.values_list(
            'product_id', flat=True
        )
        restaurants = (
            Restaurant.objects
            .filter(menu_items__product__id__in=required_products)
            .annotate(matching_products=Count(
                'menu_items__product', distinct=True)
            )
            .filter(matching_products=len(required_products))
        )
        return restaurants

    def save(self, *args, **kwargs):
        if self.restaurant and self.status == 'Unprocessed':
            self.status = 'Cooking'
        coordinates = fetch_coordinates(self.address)
        if coordinates:
            lon, lat = coordinates
            self.coordinates = Geo.objects.create(lat=lat, lon=lon)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self):
        return f"Заказ {self.id} на адрес {self.address}"


class OrderProduct(models.Model):
    product = models.ForeignKey(
        Product,
        null=True,
        verbose_name='продукт',
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена за штуку',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        blank=True
    )
    quantity = models.PositiveIntegerField(
        'количество',
        validators=[MinValueValidator(1)]
    )
    order = models.ForeignKey(
        Order,
        related_name='order_list',
        on_delete=models.CASCADE,
        verbose_name="Заказ",
        db_index=True
    )

    class Meta:
        verbose_name = 'элемент заказа'
        verbose_name_plural = 'элементы заказа'

    def __str__(self):
        return f"{self.product.name} x {self.quantity} для заказа {self.order.id}" # noqa
