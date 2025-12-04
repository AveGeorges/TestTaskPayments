from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import PayoutRequest
from .services import PayoutService

User = get_user_model()


@patch('payments.tasks.process_payout_async.delay')
class PayoutRequestModelTest(TestCase):
    """Тесты модели PayoutRequest."""
    
    def test_create_payout_request(self, mock_celery):
        """Тест создания заявки."""
        payout = PayoutRequest.objects.create(
            amount=Decimal('1000.00'),
            currency='RUB',
            recipient_details={'type': 'card', 'number': '4111111111111111'},
            description='Test payment'
        )
        
        self.assertIsNotNone(payout.external_id)
        self.assertEqual(payout.status, PayoutRequest.Status.PENDING)
        self.assertEqual(payout.amount, Decimal('1000.00'))
    
    def test_is_final_status(self, mock_celery):
        """Тест проверки финального статуса."""
        payout = PayoutRequest.objects.create(
            amount=Decimal('100'),
            currency='RUB',
            recipient_details={'type': 'card', 'number': '4111111111111111'}
        )
        
        self.assertFalse(payout.is_final_status)
        
        payout.status = PayoutRequest.Status.COMPLETED
        self.assertTrue(payout.is_final_status)


class PayoutAPITest(APITestCase):
    """Тесты REST API."""
    
    def setUp(self):
        """Создание админа для тестов."""
        self.admin, _ = User.objects.get_or_create(
            username='testadmin',
            defaults={
                'email': 'testadmin@test.com',
                'is_staff': True,
                'is_superuser': True,
            }
        )
        self.admin.set_password('testpass123')
        self.admin.save()
        self.client.force_authenticate(user=self.admin)
        
        self.valid_payload = {
            'amount': '1500.00',
            'currency': 'RUB',
            'recipient_details': {
                'type': 'card',
                'number': '4111111111111111',
                'holder': 'Test User'
            },
            'description': 'Test payout'
        }
    
    @patch('payments.tasks.process_payout_async.delay')
    def test_create_payout_success(self, mock_celery):
        """Тест успешного создания заявки."""
        response = self.client.post('/api/v1/payouts/', self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['status'], 'pending')
        self.assertEqual(response.data['currency'], 'RUB')
        self.assertIn('external_id', response.data)
    
    @patch('payments.tasks.process_payout_async.delay')
    def test_celery_task_called_on_create(self, mock_celery):
        """Тест вызова Celery-задачи при создании заявки."""
        response = self.client.post('/api/v1/payouts/', self.valid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        mock_celery.assert_called_once()
        
        call_args = mock_celery.call_args[0]
        self.assertEqual(call_args[0], response.data['external_id'])
    
    @patch('payments.tasks.process_payout_async.delay')
    def test_create_payout_invalid_recipient(self, mock_celery):
        """Тест валидации реквизитов получателя."""
        invalid_payload = self.valid_payload.copy()
        invalid_payload['recipient_details'] = {'invalid': 'data'}
        
        response = self.client.post('/api/v1/payouts/', invalid_payload, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('recipient_details', response.data)
    
    @patch('payments.tasks.process_payout_async.delay')
    def test_get_payout_by_external_id(self, mock_celery):
        """Тест получения заявки по external_id."""
        create_response = self.client.post('/api/v1/payouts/', self.valid_payload, format='json')
        external_id = create_response.data['external_id']
        
        response = self.client.get(f'/api/v1/payouts/{external_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['external_id'], external_id)
    
    @patch('payments.tasks.process_payout_async.delay')
    def test_update_payout_status(self, mock_celery):
        """Тест обновления статуса заявки."""
        create_response = self.client.post('/api/v1/payouts/', self.valid_payload, format='json')
        external_id = create_response.data['external_id']
        
        response = self.client.patch(
            f'/api/v1/payouts/{external_id}/',
            {'status': 'processing'},
            format='json'
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'processing')
    
    @patch('payments.tasks.process_payout_async.delay')
    def test_cannot_delete_processing_payout(self, mock_celery):
        """Тест запрета удаления заявки в обработке."""
        create_response = self.client.post('/api/v1/payouts/', self.valid_payload, format='json')
        external_id = create_response.data['external_id']
        
        PayoutRequest.objects.filter(external_id=external_id).update(
            status=PayoutRequest.Status.PROCESSING
        )
        
        response = self.client.delete(f'/api/v1/payouts/{external_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('обработке', response.data['detail'])
    
    @patch('payments.tasks.process_payout_async.delay')
    def test_delete_pending_payout(self, mock_celery):
        """Тест успешного удаления заявки в статусе pending."""
        create_response = self.client.post('/api/v1/payouts/', self.valid_payload, format='json')
        external_id = create_response.data['external_id']
        
        response = self.client.delete(f'/api/v1/payouts/{external_id}/')
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(PayoutRequest.objects.filter(external_id=external_id).exists())
    
    def test_unauthorized_access(self):
        """Тест запрета доступа без авторизации."""
        self.client.force_authenticate(user=None)
        
        response = self.client.get('/api/v1/payouts/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


@patch('payments.tasks.process_payout_async.delay')
class PayoutServiceTest(TestCase):
    """Тесты сервисного слоя."""
    
    def setUp(self):
        """Создание тестовой заявки."""
        self.payout = PayoutRequest.objects.create(
            amount=Decimal('500.00'),
            currency='USD',
            recipient_details={'type': 'card', 'number': '4111111111111111'}
        )
    
    def test_start_processing(self, mock_celery):
        """Тест начала обработки заявки."""
        result = PayoutService.start_processing(str(self.payout.external_id))
        
        self.assertIsNotNone(result)
        self.assertEqual(result.status, PayoutRequest.Status.PROCESSING)
    
    def test_start_processing_already_processed(self, mock_celery):
        """Тест повторной обработки уже обработанной заявки."""
        self.payout.status = PayoutRequest.Status.COMPLETED
        self.payout.save()
        
        result = PayoutService.start_processing(str(self.payout.external_id))
        
        self.assertIsNone(result)
    
    def test_complete_payout(self, mock_celery):
        """Тест успешного завершения выплаты."""
        result = PayoutService.complete_payout(str(self.payout.external_id))
        
        self.assertTrue(result.success)
        self.assertEqual(result.status, PayoutRequest.Status.COMPLETED)
    
    def test_fail_payout(self, mock_celery):
        """Тест неуспешного завершения выплаты."""
        result = PayoutService.fail_payout(
            str(self.payout.external_id),
            'Insufficient funds'
        )
        
        self.assertFalse(result.success)
        self.assertEqual(result.status, PayoutRequest.Status.FAILED)
        self.assertIn('Insufficient funds', result.message)
