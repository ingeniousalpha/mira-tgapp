import hashlib
import os

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from customers.models import Order, PaymentStatuses


def isset(data, columns):
    for column in columns:
        if data.get(column, None):
            return False
    return True


def order_load(order_id):
    order = get_object_or_404(Order, id=int(order_id))
    return order


def click_secret_key():
    return os.getenv("CLICK_SECRET_KEY", "")


def click_webhook_errors(request):
    click_trans_id = request.POST.get('click_trans_id', None)
    service_id = request.POST.get('service_id', None)
    order_id = request.POST.get('merchant_trans_id', None)
    amount = request.POST.get('amount', None)
    action = request.POST.get('action', None)
    error = request.POST.get('error', None)
    sign_time = request.POST.get('sign_time', None)
    sign_string = request.POST.get('sign_string', None)
    merchant_prepare_id = request.POST.get('merchant_prepare_id', None) if action is not None and action == '1' else ''

    if (
        isset(
            request.POST,
            [
                'click_trans_id',
                'service_id',
                'click_paydoc_id',
                'amount',
                'action',
                'error',
                'error_note',
                'sign_time',
                'sign_string'
            ]
        )
        or (action == '1' and isset(request.POST, ['merchant_prepare_id']))
    ):
        return {
            'error': '-8',
            'error_note': 'Error in request from click'
        }

    sign_check_string = '{}{}{}{}{}{}{}{}'.format(
        click_trans_id, service_id, click_secret_key(), order_id, merchant_prepare_id, amount, action, sign_time
    )
    encoder = hashlib.md5(sign_check_string.encode('utf-8'))
    sign_check_string = encoder.hexdigest()
    if sign_check_string != sign_string:
        return {
            'error': '-1',
            'error_note': 'Sign check failed'
        }

    if action not in ['0', '1']:
        return {
            'error': '-3',
            'error_note': 'Action not found'
        }

    order = order_load(order_id)
    if not order:
        return {
            'error': '-5',
            'error_note': 'Order does not exist'
        }

    if abs(float(amount) - float(order.total_amount) > 0.01):
        return {
            'error': '-2',
            'error_note': 'Incorrect parameter amount'
        }

    if order.payment_status == PaymentStatuses.CONFIRMED:
        return {
            'error': '-4',
            'error_note': 'Already paid'
        }

    if action == '1':
        if order_id != merchant_prepare_id:
            return {
                'error': '-6',
                'error_note': 'Transaction not found'
            }

    if order.payment_status == PaymentStatuses.REJECTED or int(error) < 0:
        return {
            'error': '-9',
            'error_note': 'Transaction cancelled'
        }

    return {
        'error': '0',
        'error_note': 'Success'
    }


def prepare(request):
    print("CLICK PREPARE METHOD STARTED")
    print(request)
    # result = click_webhook_errors(request)
    # print(f"INITIAL RESULT: {result}")
    # order_id = request.POST.get('merchant_trans_id', None)
    # print(f"ORDER_ID = {order_id}")
    # order = order_load(order_id)
    # print(f"ORDER: {order}")
    # if result['error'] == '0':
    #     order.payment_status = PaymentStatuses.WAITING
    #     order.save(update_fields=['payment_status'])
    # result['click_trans_id'] = request.POST.get('click_trans_id', None)
    # result['merchant_trans_id'] = request.POST.get('merchant_trans_id', None)
    # result['merchant_prepare_id'] = request.POST.get('merchant_trans_id', None)
    # result['merchant_confirm_id'] = request.POST.get('merchant_trans_id', None)
    # print(f"FINAL RESULT = {result}")
    # print("CLICK PREPARE METHOD FINISHED")
    # return JsonResponse(result)
    return JsonResponse(request)


def complete(request):
    print("CLICK COMPLETE METHOD STARTED")
    result = click_webhook_errors(request)
    print(f"INITIAL RESULT: {result}")
    order_id = request.POST.get('merchant_trans_id', None)
    print(f"ORDER_ID = {order_id}")
    order = order_load(order_id)
    if request.POST.get('error', None) is not None and int(request.POST.get('error', None)) < 0:
        order.payment_status = PaymentStatuses.REJECTED
        order.save(update_fields=['payment_status'])
    if result['error'] == '0':
        order.payment_status = PaymentStatuses.CONFIRMED
        order.save(update_fields=['payment_status'])
    result['click_trans_id'] = request.POST.get('click_trans_id', None)
    result['merchant_trans_id'] = request.POST.get('merchant_trans_id', None)
    result['merchant_prepare_id'] = request.POST.get('merchant_prepare_id', None)
    result['merchant_confirm_id'] = request.POST.get('merchant_prepare_id', None)
    print(f"FINAL RESULT = {result}")
    print("CLICK COMPLETE METHOD FINISHED")
    return JsonResponse(result)
