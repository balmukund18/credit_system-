from django.test import TestCase
from rest_framework.test import APITestCase
from rest_framework import status
from decimal import Decimal
from datetime import date
from .models import Customer, Loan
from .utils import calculate_emi, calculate_credit_score, round_nearest_lakh


class UtilsTestCase(TestCase):
    """Test utility functions"""

    def test_round_nearest_lakh(self):
        """Test rounding to nearest lakh"""
        self.assertEqual(round_nearest_lakh(150000), Decimal('200000'))
        self.assertEqual(round_nearest_lakh(1800000), Decimal('1800000'))
        self.assertEqual(round_nearest_lakh(1849999), Decimal('1800000'))
        self.assertEqual(round_nearest_lakh(1850000), Decimal('1900000'))

    def test_calculate_emi(self):
        """Test EMI calculation"""
        # Test with 10% annual rate, 12 months, 100000 principal
        emi = calculate_emi(100000, 10, 12)
        expected_emi = Decimal('8791.59')  # Approximate expected value
        self.assertAlmostEqual(float(emi), float(expected_emi), places=0)

    def test_calculate_emi_zero_rate(self):
        """Test EMI calculation with zero interest rate"""
        emi = calculate_emi(120000, 0, 12)
        expected_emi = Decimal('10000.00')  # 120000 / 12
        self.assertEqual(emi, expected_emi)

    def test_calculate_credit_score(self):
        """Test credit score calculation"""
        # Create a customer
        customer = Customer.objects.create(
            customer_id=1,
            first_name="Test",
            last_name="User",
            age=30,
            phone_number="1234567890",
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('1000000'),
            current_debt=Decimal('200000')
        )

        # Create some loans
        Loan.objects.create(
            loan_id=1,
            customer=customer,
            loan_amount=Decimal('100000'),
            tenure=12,
            interest_rate=Decimal('10.00'),
            monthly_repayment=Decimal('8791.59'),
            emis_paid_on_time=12,
            start_date=date(2023, 1, 1),
            end_date=date(2023, 12, 31)
        )

        score = calculate_credit_score(customer)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_calculate_credit_score_debt_exceeds_limit(self):
        """Test credit score when debt exceeds approved limit"""
        customer = Customer.objects.create(
            customer_id=2,
            first_name="Test",
            last_name="User2",
            age=30,
            phone_number="1234567891",
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('100000'),
            current_debt=Decimal('150000')  # Exceeds limit
        )

        score = calculate_credit_score(customer)
        self.assertEqual(score, 0)


class APITestCase(APITestCase):
    """Test API endpoints"""

    def test_register_customer(self):
        """Test customer registration API"""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 30,
            "monthly_income": 50000,
            "phone_number": "9999999999"
        }
        
        response = self.client.post('/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('customer_id', response.data)
        self.assertIn('approved_limit', response.data)
        
        # Check if customer was created
        customer = Customer.objects.get(customer_id=response.data['customer_id'])
        self.assertEqual(customer.first_name, "John")
        self.assertEqual(customer.last_name, "Doe")

    def test_register_customer_invalid_data(self):
        """Test customer registration with invalid data"""
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "age": 15,  # Invalid age (less than 18)
            "monthly_income": 50000,
            "phone_number": "9999999999"
        }
        
        response = self.client.post('/register', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_check_eligibility(self):
        """Test loan eligibility check API"""
        # First create a customer
        customer = Customer.objects.create(
            customer_id=1,
            first_name="John",
            last_name="Doe",
            age=30,
            phone_number="9999999999",
            monthly_salary=Decimal('50000'),
            approved_limit=Decimal('1800000'),
            current_debt=Decimal('0')
        )

        data = {
            "customer_id": 1,
            "loan_amount": 300000,
            "interest_rate": 10,
            "tenure": 24
        }
        
        response = self.client.post('/check-eligibility', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('approval', response.data)
        self.assertIn('interest_rate', response.data)
        self.assertIn('corrected_interest_rate', response.data)
        self.assertIn('monthly_installment', response.data)

    def test_check_eligibility_nonexistent_customer(self):
        """Test loan eligibility check for non-existent customer"""
        data = {
            "customer_id": 999,
            "loan_amount": 300000,
            "interest_rate": 10,
            "tenure": 24
        }
        
        response = self.client.post('/check-eligibility', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
