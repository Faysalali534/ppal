from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.forms import PayPalPaymentsForm
from rest_framework.views import APIView
from django.contrib import messages
from django.conf import settings
from decimal import Decimal
from paypal.standard.forms import PayPalPaymentsForm

import requests
from urllib import parse


class PayPalProcessPayment(APIView):

	def post(self, request):
		try:
			host = request.get_host()
			request_data = request.POST
			email = request_data.get('email', '')
			amount = float(request_data.get('amount', '0'))
			version = 93

			# need to store amount and version in database along with TOKEN to get the values in return url

			data = {
				'USER': settings.PAYPAL_RECIEVER_EMAIL,
				'PWD': settings.PAYPAL_PW,
				'SIGNATURE': settings.PAYPAL_SIGNATURE,
				'SUBJECT': email,
				'METHOD': 'SetExpressCheckout',
				'VERSION': version,
				'PAYMENTREQUEST_0_PAYMENTACTION': 'SALE',
				'PAYMENTREQUEST_0_AMT': amount,
				'PAYMENTREQUEST_0_CURRENCYCODE': 'USD',
				'RETURNURL': 'http://{}{}'.format(host, reverse('return')),
				'CANCELURL': 'http://{}{}'.format(host, reverse('cancel')),
			}
			response = requests.post(settings.PAYPAL_SANDBOX_URL, data=data)
			token = dict(parse.parse_qsl(response.text))['TOKEN']
			url = settings.PROCESS_PAYMENT_URL_SANDBOX.format(token)
			return JsonResponse({'url': url, 'status': 'success'})
		except Exception as e:
			return JsonResponse({'url': '', 'status': 'failed'})


class PayPalPaymentReturn(APIView):
	@csrf_exempt
	def get(self, request):
		try:
			request_data = request.GET
			TOKEN = request_data.get('token')

			# get from database
			version = 93
			amount = 100

			data = {
				'USER': settings.PAYPAL_RECIEVER_EMAIL,
				'PWD': settings.PAYPAL_PW,
				'SIGNATURE': settings.PAYPAL_SIGNATURE,
				'SUBJECT': 'm.qasim.nu@hotmail.com',
				'METHOD': 'GetExpressCheckoutDetails',
				'VERSION': version,
				'TOKEN': TOKEN
			}

			response = requests.post('https://api-3t.sandbox.paypal.com/nvp', data=data)
			result = dict(parse.parse_qsl(response.text))
			payerID = result['PAYERID']

			data = {
				'USER': settings.PAYPAL_RECIEVER_EMAIL,
				'PWD': settings.PAYPAL_PW,
				'SIGNATURE': settings.PAYPAL_SIGNATURE,
				'SUBJECT': 'm.qasim.nu@hotmail.com',
				'METHOD': 'DoExpressCheckoutPayment',
				'VERSION': version,
				'TOKEN': TOKEN,
				'PAYERID': payerID,
				'PAYMENTREQUEST_0_PAYMENTACTION': 'SALE',
				'PAYMENTREQUEST_0_AMT': amount,
				'PAYMENTREQUEST_0_CURRENCYCODE': 'USD',
			}

			response = requests.post('https://api-3t.sandbox.paypal.com/nvp', data=data)
			result = dict(parse.parse_qsl(response.text))
			status = result['ACK']
			if status == 'Success':
				return render(request, 'paypal_return.html')
			else:
				return render(request, 'payment_failure.html')
		except Exception as e:
			return render(request, 'payment_failure.html')


class PayPalPaymentCancel(APIView):
	@csrf_exempt
	def get(self, request):
		try:
			print(request)
			return render(request, 'paypal_cancel.html')
		except Exception as e:
			return render(request, 'paypal_cancel.html')