from rest_framework import serializers
from decimal import Decimal
from .models import Customer, Loan
from .utils import round_nearest_lakh


class CustomerRegistrationSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=50)
    last_name = serializers.CharField(max_length=50)
    age = serializers.IntegerField(min_value=18, max_value=100)
    monthly_income = serializers.DecimalField(max_digits=10, decimal_places=2, min_value=0)
    phone_number = serializers.CharField(max_length=15)

    def create(self, validated_data):
        # Generate customer_id (you might want to use a different strategy in production)
        last_customer = Customer.objects.order_by('-customer_id').first()
        customer_id = (last_customer.customer_id + 1) if last_customer else 1
        
        # Calculate approved limit
        approved_limit = round_nearest_lakh(36 * validated_data['monthly_income'])
        
        customer = Customer.objects.create(
            customer_id=customer_id,
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            age=validated_data['age'],
            phone_number=validated_data['phone_number'],
            monthly_salary=validated_data['monthly_income'],
            approved_limit=approved_limit,
            current_debt=Decimal('0.00')
        )
        return customer


class CustomerRegistrationResponseSerializer(serializers.ModelSerializer):
    monthly_income = serializers.DecimalField(source='monthly_salary', max_digits=10, decimal_places=2)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Customer
        fields = ['customer_id', 'name', 'age', 'monthly_income', 'approved_limit', 'phone_number']

    def get_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"


class CheckEligibilitySerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    tenure = serializers.IntegerField(min_value=1, max_value=120)


class CheckEligibilityResponseSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    approval = serializers.BooleanField()
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    corrected_interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    tenure = serializers.IntegerField()
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)


class CreateLoanSerializer(serializers.Serializer):
    customer_id = serializers.IntegerField()
    loan_amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=0)
    interest_rate = serializers.DecimalField(max_digits=5, decimal_places=2, min_value=0)
    tenure = serializers.IntegerField(min_value=1, max_value=120)


class CreateLoanResponseSerializer(serializers.Serializer):
    loan_id = serializers.IntegerField()
    customer_id = serializers.IntegerField()
    loan_approved = serializers.BooleanField()
    message = serializers.CharField()
    monthly_installment = serializers.DecimalField(max_digits=10, decimal_places=2)


class CustomerDetailSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='customer_id')

    class Meta:
        model = Customer
        fields = ['id', 'first_name', 'last_name', 'phone_number', 'age']


class LoanDetailSerializer(serializers.ModelSerializer):
    customer = CustomerDetailSerializer(read_only=True)
    monthly_installment = serializers.DecimalField(source='monthly_repayment', max_digits=10, decimal_places=2)

    class Meta:
        model = Loan
        fields = ['loan_id', 'customer', 'loan_amount', 'interest_rate', 'monthly_installment', 'tenure']


class CustomerLoansSerializer(serializers.ModelSerializer):
    monthly_installment = serializers.DecimalField(source='monthly_repayment', max_digits=10, decimal_places=2)
    repayments_left = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = ['loan_id', 'loan_amount', 'interest_rate', 'monthly_installment', 'repayments_left']

    def get_repayments_left(self, obj):
        return max(0, obj.tenure - obj.emis_paid_on_time)
