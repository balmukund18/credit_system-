from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from django.db.models import Sum, Q
import math


def round_nearest_lakh(amount):
    """Round to the nearest lakh (100,000)"""
    amount = Decimal(str(amount))
    lakh = Decimal('100000')
    return (amount / lakh).quantize(Decimal('1'), rounding=ROUND_HALF_UP) * lakh


def calculate_emi(principal, annual_rate, n_months):
    """
    Calculate EMI using the formula:
    EMI = [P x R x (1+R)^N] / [(1+R)^N - 1]
    where P = Principal, R = Monthly interest rate, N = Number of months
    """
    if annual_rate == 0:
        return principal / n_months
    
    principal = Decimal(str(principal))
    annual_rate = Decimal(str(annual_rate))
    n_months = Decimal(str(n_months))
    
    monthly_rate = annual_rate / (Decimal('12') * Decimal('100'))  # Convert to monthly decimal rate
    
    # Calculate (1 + R)^N
    one_plus_r = Decimal('1') + monthly_rate
    one_plus_r_power_n = one_plus_r ** n_months
    
    # Calculate EMI
    numerator = principal * monthly_rate * one_plus_r_power_n
    denominator = one_plus_r_power_n - Decimal('1')
    
    emi = numerator / denominator
    return emi.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def calculate_credit_score(customer, loans_queryset=None):
    """
    Calculate credit score based on:
    - % EMIs paid on time (35 points)
    - Number of past loans (20 points)
    - Loan activity in current year (20 points)
    - Loan volume vs approved limit (25 points)
    """
    if loans_queryset is None:
        loans_queryset = customer.loans.all()
    
    # If total current debt exceeds approved limit, score = 0
    if customer.current_debt > customer.approved_limit:
        return 0
    
    score = 0
    
    # 1. EMIs paid on time (35 points max)
    total_emis = loans_queryset.aggregate(
        total_emis=Sum('tenure'),
        paid_on_time=Sum('emis_paid_on_time')
    )
    
    if total_emis['total_emis'] and total_emis['total_emis'] > 0:
        emi_percentage = (total_emis['paid_on_time'] or 0) / total_emis['total_emis']
        score += min(35, int(emi_percentage * 35))
    
    # 2. Number of past loans (20 points max)
    loan_count = loans_queryset.count()
    if loan_count > 0:
        # More loans = better history, but cap at 20 points
        score += min(20, loan_count * 2)
    
    # 3. Loan activity in current year (20 points max)
    current_year = datetime.now().year
    current_year_loans = loans_queryset.filter(start_date__year=current_year).count()
    if current_year_loans > 0:
        score += min(20, current_year_loans * 5)
    
    # 4. Loan volume vs approved limit (25 points max)
    if customer.approved_limit > 0:
        volume_ratio = customer.current_debt / customer.approved_limit
        if volume_ratio <= Decimal('0.5'):  # Less than 50% utilization
            score += 25
        elif volume_ratio <= Decimal('0.75'):  # 50-75% utilization
            score += 15
        elif volume_ratio <= Decimal('1.0'):  # 75-100% utilization
            score += 5
        # Above 100% already handled above (returns 0)
    
    return min(100, max(0, score))
