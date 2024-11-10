from django.http import JsonResponse
from django.templatetags.static import static
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import ModelSerializer
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
    phone_number = PhoneNumberField(region="RU")
    products = OrderProductSerializer(
        many=True, allow_empty=False
    )

    class Meta:
        model = Order
        fields = [
            'first_name', 'last_name', 'phone_number', 'address', 'products'
        ]

    def to_internal_value(self, data):
        data['first_name'] = data.pop('firstname', None)
        data['last_name'] = data.pop('lastname', None)
        data['phone_number'] = data.pop('phonenumber', None)
        return super().to_internal_value(data)

    def create(self, validated_data):
        products_data = validated_data.pop('products')
        order = Order.objects.create(**validated_data)
        for product_data in products_data:
            OrderProduct.objects.create(
                order=order,
                product=product_data['product'],
                quantity=product_data['quantity']
            )
        return order


@api_view(['POST'])
def register_order(request):
    serializer = OrderSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': 'Заказ сформирован успешно'})
    return Response(serializer.errors, status=400)
