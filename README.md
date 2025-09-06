# Credit System - Loan Approval System

A fully functional Django + DRF + Celery + Docker based credit approval system that implements loan eligibility checks, customer registration, and loan management.

## 🚀 Features

- **Customer Registration** with automatic credit limit calculation
- **Loan Eligibility Check** with dynamic credit scoring
- **Loan Creation** with approval workflow
- **Excel Data Ingestion** using Celery background tasks
- **RESTful APIs** with proper serialization
- **PostgreSQL Database** with proper decimal handling
- **Redis + Celery** for background task processing
- **Fully Dockerized** with one-command deployment
- **Unit Tests** for critical functionality

## 📦 Technology Stack

- **Backend**: Django 4.2+, Django Rest Framework
- **Database**: PostgreSQL
- **Task Queue**: Celery + Redis
- **Data Processing**: pandas, openpyxl
- **Containerization**: Docker + docker-compose
- **Web Server**: Gunicorn

## 🏗️ Project Structure

```
credit_system/
├── credit_system/           # Django project settings
│   ├── __init__.py
│   ├── celery.py           # Celery configuration
│   ├── settings.py         # Django settings
│   ├── urls.py             # Main URL routing
│   └── wsgi.py             # WSGI application
├── loans/                   # Main application
│   ├── migrations/         # Database migrations
│   ├── management/
│   │   └── commands/
│   │       └── enqueue_ingest.py  # Data ingestion command
│   ├── __init__.py
│   ├── admin.py           # Django admin configuration
│   ├── apps.py            # App configuration
│   ├── models.py          # Database models
│   ├── serializers.py     # API serializers
│   ├── views.py           # API views
│   ├── urls.py            # App URL routing
│   ├── tasks.py           # Celery tasks
│   ├── utils.py           # Utility functions
│   └── tests.py           # Unit tests
├── data/                   # Excel data files (mounted)
│   ├── customer_data.xlsx
│   └── loan_data.xlsx
├── Dockerfile             # Docker image configuration
├── docker-compose.yml     # Multi-container setup
├── requirements.txt       # Python dependencies
├── manage.py             # Django management script
├── .env                  # Environment variables
├── .env.example          # Environment template
└── README.md             # This file
```

## 🗄️ Database Models

### Customer
- `customer_id`: Unique identifier
- `first_name`, `last_name`: Name fields
- `age`: Customer age
- `phone_number`: Contact information
- `monthly_salary`: Monthly income
- `approved_limit`: Credit limit (calculated as 36x monthly salary, rounded to nearest lakh)
- `current_debt`: Outstanding loan amount
- `created_at`: Registration timestamp

### Loan
- `loan_id`: Unique loan identifier
- `customer`: Foreign key to Customer
- `loan_amount`: Principal amount
- `tenure`: Loan duration in months
- `interest_rate`: Annual interest rate
- `monthly_repayment`: EMI amount
- `emis_paid_on_time`: Number of EMIs paid punctually
- `start_date`, `end_date`: Loan period
- `created_at`: Creation timestamp

## 🧮 Credit Scoring Algorithm

The system calculates a credit score (0-100) based on:

1. **EMIs Paid On Time (35 points)**: Percentage of EMIs paid punctually
2. **Number of Past Loans (20 points)**: Credit history depth
3. **Loan Activity in Current Year (20 points)**: Recent credit activity
4. **Loan Volume vs Approved Limit (25 points)**: Credit utilization ratio

### Approval Rules
- **Score > 50**: Approved with requested interest rate
- **30 < Score ≤ 50**: Approved with minimum 12% interest rate
- **10 < Score ≤ 30**: Approved with minimum 16% interest rate
- **Score ≤ 10**: Not approved

## 🌐 API Endpoints

### 1. POST `/register`
Register a new customer.

**Request:**
```json
{
    "first_name": "Ravi",
    "last_name": "Kumar",
    "age": 25,
    "monthly_income": 50000,
    "phone_number": "9999999999"
}
```

**Response:**
```json
{
    "customer_id": 1,
    "name": "Ravi Kumar",
    "age": 25,
    "monthly_income": 50000.00,
    "approved_limit": 1800000.00,
    "phone_number": "9999999999"
}
```

### 2. POST `/check-eligibility`
Check loan eligibility for a customer.

**Request:**
```json
{
    "customer_id": 1,
    "loan_amount": 300000,
    "interest_rate": 10,
    "tenure": 24
}
```

**Response:**
```json
{
    "customer_id": 1,
    "approval": true,
    "interest_rate": 10.00,
    "corrected_interest_rate": 12.00,
    "tenure": 24,
    "monthly_installment": 14204.28
}
```

### 3. POST `/create-loan`
Create a new loan after eligibility check.

**Request:**
```json
{
    "customer_id": 1,
    "loan_amount": 300000,
    "interest_rate": 10,
    "tenure": 24
}
```

**Response:**
```json
{
    "loan_id": 1,
    "customer_id": 1,
    "loan_approved": true,
    "message": "Loan approved with corrected interest rate: 12.00%",
    "monthly_installment": 14204.28
}
```

### 4. GET `/view-loan/{loan_id}`
View details of a specific loan.

**Response:**
```json
{
    "loan_id": 1,
    "customer": {
        "id": 1,
        "first_name": "Ravi",
        "last_name": "Kumar",
        "phone_number": "9999999999",
        "age": 25
    },
    "loan_amount": 300000.00,
    "interest_rate": 12.00,
    "monthly_installment": 14204.28,
    "tenure": 24
}
```

### 5. GET `/view-loans/{customer_id}`
View all loans for a customer.

**Response:**
```json
[
    {
        "loan_id": 1,
        "loan_amount": 300000.00,
        "interest_rate": 12.00,
        "monthly_installment": 14204.28,
        "repayments_left": 4
    }
]
```

## 🔧 Setup and Installation

### Prerequisites
- Docker
- docker-compose

### Quick Start

1. **Clone the repository:**
```bash
git clone https://github.com/your-username/credit_system.git
cd credit_system
```

2. **Copy environment configuration:**
```bash
cp .env.example .env
```

3. **Place Excel data files:**
Place your `customer_data.xlsx` and `loan_data.xlsx` files in the `./data/` directory.
   
   **Note:** Sample CSV files are provided in the data directory. Convert them to Excel format or use your own data files with the same column structure.

4. **Build and start services:**
```bash
docker-compose up --build -d
```

5. **Run database migrations:**
```bash
docker-compose exec web python manage.py migrate
```

6. **Ingest Excel data (optional):**
```bash
docker-compose exec web python manage.py enqueue_ingest
```

7. **Create superuser (optional):**
```bash
docker-compose exec web python manage.py createsuperuser
```

### Access Points
- **API**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

## 🧪 Testing

### Run Unit Tests
```bash
docker-compose exec web python manage.py test
```

### API Testing with curl

**Register Customer:**
```bash
curl -X POST http://localhost:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "Ravi",
    "last_name": "Kumar",
    "age": 25,
    "monthly_income": 50000,
    "phone_number": "9999999999"
  }'
```

**Check Eligibility:**
```bash
curl -X POST http://localhost:8000/check-eligibility \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 300000,
    "interest_rate": 10,
    "tenure": 24
  }'
```

**Create Loan:**
```bash
curl -X POST http://localhost:8000/create-loan \
  -H "Content-Type: application/json" \
  -d '{
    "customer_id": 1,
    "loan_amount": 300000,
    "interest_rate": 10,
    "tenure": 24
  }'
```

**View Loan:**
```bash
curl http://localhost:8000/view-loan/1
```

**View Customer Loans:**
```bash
curl http://localhost:8000/view-loans/1
```

## 📊 Excel Data Format

### customer_data.xlsx
| customer_id | first_name | last_name | age | phone_number | monthly_salary | approved_limit | current_debt |
|-------------|------------|-----------|-----|--------------|----------------|----------------|--------------|
| 1           | Ravi       | Kumar     | 25  | 9999999999   | 50000.00       | 1800000.00     | 0.00         |

### loan_data.xlsx
| loan_id | customer_id | loan_amount | tenure | interest_rate | monthly_repayment | emis_paid_on_time | start_date | end_date   |
|---------|-------------|-------------|--------|---------------|-------------------|-------------------|------------|------------|
| 1       | 1           | 300000.00   | 24     | 10.50         | 14500.00          | 20                | 2023-01-15 | 2024-12-15 |

## 🔍 Monitoring and Logs

**View application logs:**
```bash
docker-compose logs web
```

**View Celery worker logs:**
```bash
docker-compose logs worker
```

**View database logs:**
```bash
docker-compose logs db
```

## 🛠️ Development

### Local Development Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Set up environment variables:**
```bash
cp .env.example .env
# Edit .env with your local configuration
```

3. **Start PostgreSQL and Redis:**
```bash
docker-compose up db redis -d
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Start development server:**
```bash
python manage.py runserver
```

6. **Start Celery worker:**
```bash
celery -A credit_system worker --loglevel=info
```

## 🔒 Production Considerations

- Change default passwords and secret keys
- Use environment-specific configurations
- Set up proper logging and monitoring
- Configure backup strategies for database
- Use a reverse proxy (nginx) for production
- Implement rate limiting and authentication
- Set up SSL certificates

## 📝 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📞 Support

For support and questions, please create an issue in the repository.
