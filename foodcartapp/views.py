from django.http import JsonResponse
from django.templatetags.static import static
from django.core.exceptions import ValidationError
import json
from phonenumber_field.phonenumber import to_python
from phonenumbers import NumberParseException

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


def register_order(request):
    try:
        frontend_order = json.loads(request.body.decode())
        phonenumber = to_python(frontend_order['phonenumber'])
        if not phonenumber or not phonenumber.is_valid():
            raise ValidationError('Номер телефона недействителен')
        order = Order.objects.create(
            first_name=frontend_order['firstname'],
            last_name=frontend_order['lastname'],
            phone_number=phonenumber,
            address=frontend_order['address']
        )
        for product_order in frontend_order['products']:
            OrderProduct.objects.create(
                product=Product.objects.get(id=product_order['product']),
                quantity=product_order['quantity'],
                order=order
            )
        return JsonResponse({
           'success': 'Заказ сформирован успешно'
        })
    except (NumberParseException, ValidationError):
        return JsonResponse({
            'error': 'Неверный номер телефона'
        },
            status=400)
    except Exception:
        return JsonResponse({
           'error': 'Возникла какая-то ошибка. Попробуйте ещё раз'
        })
