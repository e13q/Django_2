from django.http import JsonResponse
from django.templatetags.static import static
from django.db import transaction
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from phonenumber_field.serializerfields import PhoneNumberField

from .models import Product
from .models import OrderProduct
from .models import Order


def banners_list_api(request):
    # FIXME move data to db?
    return JsonResponse([
        {
            'title': 'Burger',
            'src': static('burger.jpg'),
            'text': 'Tasty Burger at your door step',
        },
        {
            'title': 'Spices',
            'src': static('food.jpg'),
            'text': 'All Cuisines',
        },
        {
            'title': 'New York',
            'src': static('tasty.jpg'),
            'text': 'Food is incomplete without a tasty dessert',
        }
    ], safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


def product_list_api(request):
    products = Product.objects.select_related('category').available()

    dumped_products = []
    for product in products:
        dumped_product = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'special_status': product.special_status,
            'description': product.description,
            'category': {
                'id': product.category.id,
                'name': product.category.name,
            } if product.category else None,
            'image': product.image.url,
            'restaurant': {
                'id': product.id,
                'name': product.name,
            }
        }
        dumped_products.append(dumped_product)
    return JsonResponse(dumped_products, safe=False, json_dumps_params={
        'ensure_ascii': False,
        'indent': 4,
    })


class OrderProductSerializer(ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    phone_number = PhoneNumberField(region="RU", source='phonenumber')
    first_name = serializers.CharField(source='firstname')
    last_name = serializers.CharField(source='lastname')
    products = OrderProductSerializer(
        many=True, allow_empty=False, write_only=True
    )
    order_list = SerializerMethodField(read_only=True, source='items')

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'phone_number', 'address', 'products', 'order_list'
        ]
        extra_kwargs = {
            'order_list': {'read_only': True}
        }

    def create(self, validated_data):
        order_list = validated_data.pop('products')
        with transaction.atomic():
            order = Order.objects.create(**validated_data)
            for product in order_list:
                OrderProduct.objects.create(
                    order=order,
                    product=product['product'],
                    quantity=product['quantity'],
                    price=product['product'].price
                )
            return order

    def get_order_list(self, obj):
        products = obj.order_list.all()
        return OrderProductSerializer(products, many=True).data


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=400)
