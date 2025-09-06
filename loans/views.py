from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from decimal import Decimal
from datetime import date, timedelta
from .models import Customer, Loan
from .serializers import (
    CustomerRegistrationSerializer, CustomerRegistrationResponseSerializer,
    CheckEligibilitySerializer, CheckEligibilityResponseSerializer,
    CreateLoanSerializer, CreateLoanResponseSerializer,
    LoanDetailSerializer, CustomerLoansSerializer
)
from .utils import calculate_credit_score, calculate_emi


@api_view(['POST'])
def register_customer(request):
    """Register a new customer"""
    serializer = CustomerRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        customer = serializer.save()
        response_serializer = CustomerRegistrationResponseSerializer(customer)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def check_eligibility(request):
    """Check loan eligibility for a customer"""
    serializer = CheckEligibilitySerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    try:
        customer = Customer.objects.get(customer_id=data['customer_id'])
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Calculate credit score
    loans_queryset = customer.loans.all()
    credit_score = calculate_credit_score(customer, loans_queryset)
    
    # Determine approval and corrected interest rate
    approval = False
    corrected_interest_rate = data['interest_rate']
    
    if credit_score > 50:
        approval = True
    elif 30 < credit_score <= 50:
        if data['interest_rate'] >= 12:
            approval = True
        else:
            approval = True
            corrected_interest_rate = Decimal('12.00')
    elif 10 < credit_score <= 30:
        if data['interest_rate'] >= 16:
            approval = True
        else:
            approval = True
            corrected_interest_rate = Decimal('16.00')
    else:  # credit_score <= 10
        approval = False
    
    # Calculate monthly installment using corrected interest rate
    monthly_installment = Decimal('0.00')
    if approval:
        monthly_installment = calculate_emi(
            data['loan_amount'],
            corrected_interest_rate,
            data['tenure']
        )
    
    response_data = {
        'customer_id': data['customer_id'],
        'approval': approval,
        'interest_rate': data['interest_rate'],
        'corrected_interest_rate': corrected_interest_rate,
        'tenure': data['tenure'],
        'monthly_installment': monthly_installment
    }
    
    response_serializer = CheckEligibilityResponseSerializer(data=response_data)
    if response_serializer.is_valid():
        return Response(response_serializer.data, status=status.HTTP_200_OK)
    return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def create_loan(request):
    """Create a new loan if customer is eligible"""
    serializer = CreateLoanSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    data = serializer.validated_data
    try:
        customer = Customer.objects.get(customer_id=data['customer_id'])
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check eligibility
    loans_queryset = customer.loans.all()
    credit_score = calculate_credit_score(customer, loans_queryset)
    
    # Determine approval and corrected interest rate (same logic as check_eligibility)
    approval = False
    corrected_interest_rate = data['interest_rate']
    message = "Loan not approved due to low credit score"
    
    if credit_score > 50:
        approval = True
        message = "Loan approved"
    elif 30 < credit_score <= 50:
        if data['interest_rate'] >= 12:
            approval = True
            message = "Loan approved"
        else:
            approval = True
            corrected_interest_rate = Decimal('12.00')
            message = f"Loan approved with corrected interest rate: {corrected_interest_rate}%"
    elif 10 < credit_score <= 30:
        if data['interest_rate'] >= 16:
            approval = True
            message = "Loan approved"
        else:
            approval = True
            corrected_interest_rate = Decimal('16.00')
            message = f"Loan approved with corrected interest rate: {corrected_interest_rate}%"
    
    monthly_installment = Decimal('0.00')
    loan_id = None
    
    if approval:
        # Calculate monthly installment
        monthly_installment = calculate_emi(
            data['loan_amount'],
            corrected_interest_rate,
            data['tenure']
        )
        
        # Generate loan_id
        last_loan = Loan.objects.order_by('-loan_id').first()
        loan_id = (last_loan.loan_id + 1) if last_loan else 1
        
        # Create loan
        start_date = date.today()
        end_date = start_date + timedelta(days=data['tenure'] * 30)  # Approximate
        
        loan = Loan.objects.create(
            loan_id=loan_id,
            customer=customer,
            loan_amount=data['loan_amount'],
            tenure=data['tenure'],
            interest_rate=corrected_interest_rate,
            monthly_repayment=monthly_installment,
            start_date=start_date,
            end_date=end_date
        )
        
        # Update customer's current debt
        customer.current_debt += data['loan_amount']
        customer.save()
        
        loan_id = loan.loan_id
    
    response_data = {
        'loan_id': loan_id,
        'customer_id': data['customer_id'],
        'loan_approved': approval,
        'message': message,
        'monthly_installment': monthly_installment
    }
    
    response_serializer = CreateLoanResponseSerializer(data=response_data)
    if response_serializer.is_valid():
        return Response(response_serializer.data, status=status.HTTP_201_CREATED if approval else status.HTTP_200_OK)
    return Response(response_serializer.errors, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def view_loan(request, loan_id):
    """View details of a specific loan"""
    try:
        loan = Loan.objects.select_related('customer').get(loan_id=loan_id)
    except Loan.DoesNotExist:
        return Response({'error': 'Loan not found'}, status=status.HTTP_404_NOT_FOUND)
    
    serializer = LoanDetailSerializer(loan)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['GET'])
def view_customer_loans(request, customer_id):
    """View all loans for a specific customer"""
    try:
        customer = Customer.objects.get(customer_id=customer_id)
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    
    loans = customer.loans.all()
    serializer = CustomerLoansSerializer(loans, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
