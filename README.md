# Provider Management Backend

Django REST Framework backend for the Provider Management Tool with Flowable BPMN workflow integration.

## Tech Stack

- Python 3.x
- Django REST Framework
- SQLite (Application Data)
- PostgreSQL (Flowable Data)
- Flowable BPMN Engine 6.8.0
- JWT Authentication

## Prerequisites

- Docker & Docker Compose
- Python 3.8+

## Installation & Setup

### 1. Environment Configuration

Create a `.env` file in the `backend` directory:

```env
DJANGO_DEBUG=True
DJANGO_SECRET_KEY=django-secret-key
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1
DJANGO_BASE_URL=http://django:8000

THIRD_PARTY_API_BASE=https://domain.com

CORS_ALLOWED_ORIGINS=http://localhost:3000
CSRF_TRUSTED_ORIGINS=https://domain.com,https://*.com,http://localhost:3000

FLOWABLE_API_KEY=super-secret-flowable-key
FLOWABLE_BASE_URL=http://flowable-rest:8080/flowable-rest/service
FLOWABLE_REST_USERNAME=rest-admin
FLOWABLE_REST_PASSWORD=test
```

### 2. Run with Docker Compose

From the project root directory:

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f django

# Stop services
docker-compose down
```

### 3. Initial Setup

```bash
# Access Django container
docker exec -it provider-backend bash

# Run migrations
python manage.py migrate

# Create superuser (optional)
python manage.py createsuperuser
```

## API Endpoints

The API is available at `http://localhost:8000/api/`

### Main Routes

- `/api/auth/` - Authentication (JWT tokens)
- `/api/accounts/` - User management
- `/api/providers/` - Provider organizations
- `/api/specialists/` - Specialist profiles
- `/api/requests/` - Service requests & offers
- `/api/contracts/` - Contract negotiation
- `/api/notifications/` - User notifications
- `/api/audit/` - Audit logs

## Development

### Running Without Docker

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

### Project Structure

```
backend/
├── accounts/          # User authentication
├── audit_log/         # Activity tracking
├── config/            # Settings & configuration
├── contracts/         # Contract negotiation
├── integrations/      # Flowable integration
├── notifications/     # User notifications
├── providers/         # Provider organizations
├── service_requests/  # Requests & offers
├── specialists/       # Specialist profiles
├── .env
├── Dockerfile
└── requirements.txt
flowable/
├── contract-negotiation.bpmn20.xml
└── service-request-new.bpmn20.xml
docker-compose.yml
README.md
```

## Flowable Integration

Flowable REST API is available at `http://localhost:8080`

- Username: `rest-admin`
- Password: `test`

### Deploy BPMN Processes

```bash
# Upload BPMN files via Flowable REST API
curl --request POST \
  --url http://localhost:8080/flowable-rest/service/repository/deployments \
  --header 'authorization: Basic cmVzdC1hZG1pbjp0ZXN0' \
  --header 'content-type: multipart/form-data' \
  --form 'file=@service-request-bidding.bpmn20.xml'
```

## Troubleshooting

### Database Connection Issues

```bash
# Reset database
docker-compose down -v
docker-compose up -d
docker exec -it provider-backend python manage.py migrate
```