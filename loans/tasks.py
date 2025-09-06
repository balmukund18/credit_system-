from celery import shared_task
import pandas as pd
import os
from decimal import Decimal
from datetime import datetime
from django.utils import timezone
from .models import Customer, Loan


@shared_task
def ingest_excel_data():
    """
    Celery task to ingest customer and loan data from Excel files
    """
    data_dir = '/app/data'
    customer_file = os.path.join(data_dir, 'customer_data.xlsx')
    loan_file = os.path.join(data_dir, 'loan_data.xlsx')
    
    results = {
        'customers_created': 0,
        'customers_updated': 0,
        'loans_created': 0,
        'errors': []
    }
    
    try:
        # Process customer data
        if os.path.exists(customer_file):
            customer_df = pd.read_excel(customer_file)
            
            # Expected columns: customer_id, first_name, last_name, age, phone_number, monthly_salary, approved_limit, current_debt
            customers_to_create = []
            customers_to_update = []
            
            for index, row in customer_df.iterrows():
                try:
                    customer_data = {
                        'customer_id': int(row.get('Customer ID', 0)),
                        'first_name': str(row.get('First Name', '')),
                        'last_name': str(row.get('Last Name', '')),
                        'age': int(row.get('Age', 0)),
                        'phone_number': str(row.get('Phone Number', '')),
                        'monthly_salary': Decimal(str(row.get('Monthly Salary', 0))),
                        'approved_limit': Decimal(str(row.get('Approved Limit', 0))),
                        'current_debt': Decimal('0'),  # Set to 0 initially
                    }
                    
                    # Check if customer exists
                    try:
                        customer = Customer.objects.get(customer_id=customer_data['customer_id'])
                        # Update existing customer
                        for key, value in customer_data.items():
                            setattr(customer, key, value)
                        customers_to_update.append(customer)
                    except Customer.DoesNotExist:
                        # Create new customer
                        customers_to_create.append(Customer(**customer_data))
                
                except Exception as e:
                    results['errors'].append(f"Error processing customer row {index}: {str(e)}")
            
            # Bulk create/update customers
            if customers_to_create:
                Customer.objects.bulk_create(customers_to_create, ignore_conflicts=True)
                results['customers_created'] = len(customers_to_create)
            
            if customers_to_update:
                Customer.objects.bulk_update(
                    customers_to_update,
                    ['first_name', 'last_name', 'age', 'phone_number', 'monthly_salary', 'approved_limit', 'current_debt']
                )
                results['customers_updated'] = len(customers_to_update)
        
        # Process loan data
        if os.path.exists(loan_file):
            loan_df = pd.read_excel(loan_file)
            
            # Expected columns: loan_id, customer_id, loan_amount, tenure, interest_rate, monthly_repayment, emis_paid_on_time, start_date, end_date
            loans_to_create = []
            
            for index, row in loan_df.iterrows():
                try:
                    customer_id = int(row.get('Customer ID', 0))
                    
                    # Get customer
                    try:
                        customer = Customer.objects.get(customer_id=customer_id)
                    except Customer.DoesNotExist:
                        results['errors'].append(f"Customer with ID {customer_id} not found for loan row {index}")
                        continue
                    
                    # Parse dates
                    start_date = row.get('Date of Approval')
                    end_date = row.get('End Date')
                    
                    if isinstance(start_date, str):
                        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                    elif hasattr(start_date, 'date'):
                        start_date = start_date.date()
                    
                    if isinstance(end_date, str):
                        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                    elif hasattr(end_date, 'date'):
                        end_date = end_date.date()
                    
                    loan_data = {
                        'loan_id': int(row.get('Loan ID', 0)),
                        'customer': customer,
                        'loan_amount': Decimal(str(row.get('Loan Amount', 0))),
                        'tenure': int(row.get('Tenure', 0)),
                        'interest_rate': Decimal(str(row.get('Interest Rate', 0))),
                        'monthly_repayment': Decimal(str(row.get('Monthly payment', 0))),
                        'emis_paid_on_time': int(row.get('EMIs paid on Time', 0)),
                        'start_date': start_date,
                        'end_date': end_date,
                    }
                    
                    # Check if loan exists
                    if not Loan.objects.filter(loan_id=loan_data['loan_id']).exists():
                        loans_to_create.append(Loan(**loan_data))
                
                except Exception as e:
                    results['errors'].append(f"Error processing loan row {index}: {str(e)}")
            
            # Bulk create loans
            if loans_to_create:
                Loan.objects.bulk_create(loans_to_create, ignore_conflicts=True)
                results['loans_created'] = len(loans_to_create)
    
    except Exception as e:
        results['errors'].append(f"General error: {str(e)}")
    
    return results
