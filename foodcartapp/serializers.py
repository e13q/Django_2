from django.db import transaction
from rest_framework import serializers
from rest_framework.serializers import ModelSerializer, SerializerMethodField
from phonenumber_field.serializerfields import PhoneNumberField

from .models import OrderProduct
from .models import Order


class OrderProductSerializer(ModelSerializer):
    class Meta:
        model = OrderProduct
        fields = ['product', 'quantity']


class OrderSerializer(ModelSerializer):
    phonenumber = PhoneNumberField(region="RU", source='phone_number')
    firstname = serializers.CharField(source='first_name')
    lastname = serializers.CharField(source='last_name')
    products = OrderProductSerializer(
        many=True, allow_empty=False, write_only=True
    )
    order_list = SerializerMethodField(read_only=True)

    class Meta:
        model = Order
        fields = [
            'firstname', 'lastname', 'phonenumber', 'address', 'products', 'order_list'
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
