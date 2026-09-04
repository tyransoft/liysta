from decimal import Decimal
import hashlib
import hmac
import json
import requests
from django.utils import timezone
from django.conf import settings
from typing import Dict, Any, Optional
import logging
import uuid
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Payment, PaymentGatewaySetting
import base64



logger = logging.getLogger(__name__)

class EzonePayService:
   
    
    CURRENCY_MAP = {
        'LYD': 1,   
        'USD': 2,    
       
    }
    
    WEBHOOK_EVENTS = {
        'PAID': 2,           
        'FAILED': 3,       
        'REFUNDED': 4,       
        'CANCELLED': 5,     
    }
    
    def __init__(self, settings):
        
        self.settings = settings
        self.api_key = settings.api_key
        self.base_url = self._get_base_url()
        
    def _get_base_url(self) -> str:
        
            #return 'https://api.ezonepay.ly'
        
        return 'https://demo.ezonepay.ly'
    
    def _get_headers(self) -> Dict[str, str]:
       
        return {
            'X-API-Key': self.api_key,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
        }
    
    def _get_currency_id(self, currency_code: str) -> int:
      
        return self.CURRENCY_MAP.get(currency_code.upper(), 1) 
    
    
    def create_payment_link(self, payment) -> Dict[str, Any]:
     
        try:
            customer_data = {
                'FirstName': payment.customer_name.split()[0] if payment.customer_name else 'عميل',
                'LastName': ' '.join(payment.customer_name.split()[1:]) if payment.customer_name else '',
                'PhoneNumber': payment.customer_phone or '',
            }
            
            payload = {
                'Title': f'طلب #{payment.order.id} - {payment.merchant.get_full_name()}',
                'OrderReference': payment.order.order_reference or f'ORD-{payment.order.id}',
                'InternalReference': payment.payment_reference,
                'Amount': Decimal(str(payment.amount)),
                'Currency':1,
                'Note': f'دفع للطلب رقم #{payment.order.id}',
                'ExpiresAt': (timezone.now() + timezone.timedelta(hours=2)).isoformat(),
                'MaxUsageCount': 1, 
                'RedirectUrl': f"{settings.SITE_URL}/payment/return/{payment.id}/",
                'Customer': customer_data,
                'IsUniqueOrderReference': True,
            }
            

            
            response = requests.post(
                f"{self.base_url}/payment-link/new",
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            result = response.json()
            
            if response.status_code == 200:
                data = result.get('data', {})
                payment_url = data.get('url')
                reference = data.get('reference')
                
                return {
                    'success': True,
                    'payment_url': payment_url,
                    'reference': reference,
                    'transaction_id': None,  
                }
            else:
                error_message = result.get('message', 'Unknown error')
                logger.error(f"EzonePay create payment link error: {error_message}")
                return {
                    'success': False,
                    'message': error_message,
                    'code': result.get('code'),
                }
                
        except requests.RequestException as e:
            logger.error(f"EzonePay request error: {str(e)}")
            return {
                'success': False,
                'message': f'Network error: {str(e)}',
            }
        except Exception as e:
            logger.error(f"EzonePay unexpected error: {str(e)}")
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
            }


    
    def subscribe_webhook(self, url: str, event: int) -> Dict[str, Any]:
       
        try:
            payload = {
                'Url': url,
                'Event': event,
            }
            
            response = requests.post(
                f"{self.base_url}/Webhook/subscribe",
                json=payload,
                headers=self._get_headers(),
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                data = result.get('data', {})
                return {
                    'success': True,
                    'secret_key': data.get('SecretKey'),  
                    'subscription_id': data.get('Id'),
                    'data': data,
                }
            else:
                result = response.json()
                return {
                    'success': False,
                    'message': result.get('message', 'Subscription failed'),
                    'code': result.get('code'),
                }
                
        except Exception as e:
            logger.error(f"EzonePay webhook subscription error: {str(e)}")
            return {
                'success': False,
                'message': str(e),
            }
    
   
   
    
    def verify_webhook_signature(self, raw_body: str, signature: str, secret_key: str) -> bool:

        try:
            secret_bytes = secret_key.encode('utf-8')
            body_bytes = raw_body.encode('utf-8')
            
            hmac_obj = hmac.new(secret_bytes, body_bytes, hashlib.sha256)
            computed_signature = base64.b64encode(hmac_obj.digest()).decode('utf-8')
            
            return hmac.compare_digest(computed_signature, signature)
            
        except Exception as e:
            logger.error(f"Webhook signature verification error: {str(e)}")
            return False
    

    
    
    def test_connection(self) -> Dict[str, Any]:

        try:
            response = requests.get(
                f"{self.base_url}/payment-link/list",
                params={'limit': 1},
                headers=self._get_headers(),
                timeout=10
            )
            
            if response.status_code == 200:
                return {
                    'success': True,
                    'message': 'Connection successful',
                    'data': response.json(),
                }
            elif response.status_code == 401:
                return {
                    'success': False,
                    'message': 'Invalid API Key or insufficient permissions',
                }
            elif response.status_code == 403:
                return {
                    'success': False,
                    'message': 'API Key does not have required scopes (payment.link.view)',
                }
            else:
                result = response.json()
                return {
                    'success': False,
                    'message': f"API error: {result.get('message', 'Unknown error')}",
                    'code': response.status_code,
                }
                
        except requests.ConnectionError:
            return {
                'success': False,
                'message': 'Cannot connect to EzonePay API. Please check your internet connection.',
            }
        except requests.Timeout:
            return {
                'success': False,
                'message': 'Connection timeout. Please try again later.',
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'Unexpected error: {str(e)}',
            }

class PaymentService:
   
    
    @staticmethod
    def generate_reference() -> str:
       
        return f"PAY-{uuid.uuid4().hex[:12].upper()}"
    
    @staticmethod
    def save_gateway_response(payment: Payment, response: dict):
       
        if payment.gateway_response:
            if isinstance(payment.gateway_response, dict):
                payment.gateway_response.update(response)
            else:
                payment.gateway_response = response
        else:
            payment.gateway_response = response
        
        payment.save(update_fields=['gateway_response', 'updated_at'])
        logger.info(f"Saved gateway response for payment {payment.payment_reference}")
    
    @staticmethod
    def update_payment_status(payment: Payment, status: str, data: dict = None):
        status_map = {
            'pending': Payment.StatusChoices.PENDING,
            'processing': Payment.StatusChoices.PROCESSING,
            'completed': Payment.StatusChoices.COMPLETED,
            'failed': Payment.StatusChoices.FAILED,
            'refunded': Payment.StatusChoices.REFUNDED,
            'cancelled': Payment.StatusChoices.CANCELLED,
            'expired': Payment.StatusChoices.EXPIRED,
        }
        
        new_status = status_map.get(status, payment.status)
        
        if payment.status != new_status:
            payment.status = new_status
            payment.updated_at = timezone.now()
            
            if new_status == Payment.StatusChoices.COMPLETED:
                payment.paid_at = timezone.now()
            
            if data and data.get('transaction_id'):
                payment.transaction_id = data.get('transaction_id')
            
            payment.save()
            logger.info(
                f"Updated payment {payment.payment_reference} status from "
                f"{payment.status} to {new_status}"
            )
            
            return True
        return False
    
    @staticmethod
    def mark_order_paid(order):
      
        if not order.is_paid:
            order.is_paid = True
            order.paid_at = timezone.now()
            order.save()
            logger.info(f"Order #{order.id} marked as paid")
    
    @staticmethod
    def log_gateway_error(payment: Payment, action: str, error: str):
    
        error_data = {
            'action': action,
            'error': error,
            'timestamp': timezone.now().isoformat(),
        }
        
       
        logger.error(
            f"Gateway error for payment {payment.payment_reference}: "
            f"Action={action}, Error={error}"
        )
        
        if payment.gateway_response:
            if 'errors' not in payment.gateway_response:
                payment.gateway_response['errors'] = []
            payment.gateway_response['errors'].append(error_data)
            payment.save(update_fields=['gateway_response'])
    
    @staticmethod
    def notify_merchant(payment: Payment):
       
        try:
            subject = f"دفع جديد - {payment.payment_reference}"
            message = render_to_string('emails/merchant_payment_notification.txt', {
                'payment': payment,
                'order': payment.order,
            })
            html_message = render_to_string('emails/merchant_payment_notification.html', {
                'payment': payment,
                'order': payment.order,
            })
            
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [payment.merchant.user.email],
                html_message=html_message,
                fail_silently=True,
            )
            logger.info(f"Merchant notification sent for payment {payment.payment_reference}")
        except Exception as e:
            logger.error(f"Failed to send merchant notification: {str(e)}")
    
   
    @staticmethod
    def process_webhook(raw_body: str, signature: str, settings) -> dict:
      
        try:
            service = EzonePayService(settings)
            
            if not service.verify_webhook_signature(raw_body, signature, settings.webhook_secret):
                logger.warning("Invalid webhook signature")
                return {'success': False, 'message': 'Invalid signature'}
            
            payload = json.loads(raw_body)
            webhook_data = service.parse_webhook(payload)
            
            event = webhook_data.get('event')
            if event != EzonePayService.WEBHOOK_EVENTS['PAID']:
                logger.info(f"Ignoring webhook event: {event}")
                return {'success': True, 'message': 'Event ignored'}
            
            order_reference = webhook_data.get('order_reference')
            transaction_id = webhook_data.get('transaction_id')
            
            payment = Payment.objects.filter(
                order__order_reference=order_reference
            ).first()
            
            if not payment:
                logger.error(f"Payment not found for order reference: {order_reference}")
                return {'success': False, 'message': 'Payment not found'}
            
            webhook_key = f"{transaction_id}_{event}"
            if payment.gateway_response and payment.gateway_response.get('webhook_processed') == webhook_key:
                logger.info(f"Webhook already processed: {webhook_key}")
                return {'success': True, 'message': 'Already processed'}
            
            payment.transaction_id = transaction_id
            payment.status = Payment.StatusChoices.COMPLETED
            payment.paid_at = timezone.now()
            
            if not payment.gateway_response:
                payment.gateway_response = {}
            payment.gateway_response['webhook_data'] = webhook_data
            payment.gateway_response['webhook_processed'] = webhook_key
            payment.save()
            
            PaymentService.mark_order_paid(payment.order)
            
            PaymentService.notify_merchant(payment)
            
            logger.info(f"Payment completed via webhook: {payment.payment_reference}")
            return {'success': True, 'message': 'Payment updated successfully'}
            
        except json.JSONDecodeError:
            return {'success': False, 'message': 'Invalid JSON'}
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {'success': False, 'message': str(e)}
    
  