# LocalKonnect - Trusted Local Contractor Network

A Django-based web platform connecting customers with reliable local contractors through a geospatial search and trust scoring system.

## 🎯 Project Overview

LocalKonnect helps customers find trustworthy local contractors while providing contractors a platform to showcase their services and build reputation through customer reviews and trust marks.

## ✨ Implemented Features

### User Management
- ✅ Custom user model with role-based access (Customer/Contractor)
- ✅ Session-based authentication (login/logout/register)
- ✅ User profile management with location (PostGIS Point field)
- ✅ Redis-backed rate limiting for login attempts

### Contractor Features
- ✅ Contractor profile with business information
- ✅ Office location with PostGIS Point field
- ✅ Service radius configuration (km)
- ✅ Auto-profile creation via Django signals
- ✅ Verification status tracking
- ✅ Dashboard with service statistics

### Service Management
- ✅ Hierarchical service categories and subcategories
- ✅ Contractor service CRUD (Create/Read/Update/Delete)
- ✅ Per-service trust scores
- ✅ Many-to-many subcategory relationships
- ✅ Service portfolio management

### Trust & Review System
- ✅ TrustMark model (unique per customer-service pair)
- ✅ Review system linked to trust marks
- ✅ Review helpfulness voting
- ✅ Trust mark verification status
- ✅ Fraud detection framework

### Geospatial Search
- ✅ PostGIS-powered distance-based search
- ✅ Filter by category, subcategory, trust score
- ✅ Radius search (within X km of location)
- ✅ Results ordered by trust score and distance
- ✅ Redis caching for search performance

### Infrastructure
- ✅ Docker Compose setup (backend + PostgreSQL + Redis)
- ✅ PostgreSQL 15 with PostGIS 3.3
- ✅ Redis for caching and session storage
- ✅ Django admin interface
- ✅ Migration management
- ✅ GIST index on contractor locations

## 🛠️ Tech Stack

### Backend
- **Django 4.2.8** - Web framework
- **PostgreSQL 15 + PostGIS 3.3** - Database with geospatial support
- **Redis 7** - Caching layer
- **Django Redis** - Cache backend
- **Python 3.11** - Runtime

### Frontend (Server-Rendered)
- **Django Templates** - Template engine
- **Tailwind CSS** (CDN) - Styling
- **Alpine.js** - Reactive components
- **Vanilla JavaScript** - Map integration and UI

### DevOps
- **Docker & Docker Compose** - Containerization
- **Gunicorn** - WSGI server (production-ready)
- **WhiteNoise** - Static file serving

## 🚀 Quick Start

### Prerequisites
- Docker Desktop installed
- Git

### Setup Instructions

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/LocalKonnect.git
cd LocalKonnect
```

2. **Create environment file:**
```bash
# Create .env in project root (optional, defaults work for dev)
DATABASE_NAME=localkonnect_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
REDIS_URL=redis://localkonnect_redis:6379/1
```

3. **Start the application:**
```powershell
docker compose up -d --build
```

4. **Create the database and run migrations:**
```powershell
docker compose exec db psql -U postgres -c "CREATE DATABASE localkonnect_db;"
docker compose exec backend python manage.py migrate
```

5. **Create a superuser (optional):**
```powershell
docker compose exec backend python manage.py createsuperuser
```

6. **Access the application:**
- **Web Application:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin

### Stopping the Application
```powershell
docker compose down
```

### Viewing Logs
```powershell
docker compose logs backend -f
```

## 📁 Project Structure

```
LocalKonnect/
├── backend/
│   ├── config/                    # Django project settings
│   │   ├── settings.py           # Main configuration
│   │   ├── urls.py               # Root URL routing
│   │   └── celery.py             # Celery config (unused)
│   ├── apps/
│   │   ├── users/                # User authentication & profiles
│   │   │   ├── models.py         # Custom User model
│   │   │   ├── template_views.py # Login/Register views
│   │   │   ├── forms.py          # Auth forms
│   │   │   └── signals.py        # User signals
│   │   ├── contractors/          # Contractor profiles
│   │   │   ├── models.py         # ContractorProfile
│   │   │   ├── views.py          # Dashboard, CRUD
│   │   │   ├── signals.py        # Auto-create profile
│   │   │   └── utils.py          # Profile guards
│   │   ├── services/             # Service management
│   │   │   ├── models.py         # Category, Service models
│   │   │   └── admin.py          # Admin interface
│   │   ├── trust/                # Trust & review system
│   │   │   ├── models.py         # TrustMark, Review
│   │   │   ├── views.py          # Trust CRUD
│   │   │   └── fraud_detection.py
│   │   ├── search/               # Geospatial search
│   │   │   ├── views.py          # Distance search
│   │   │   └── forms.py          # Search filters
│   │   ├── customer/             # Customer features (minimal)
│   │   ├── admin_panel/          # Admin tools (minimal)
│   │   └── ai/                   # AI integration (unused)
│   ├── templates/                # Django templates
│   │   ├── base/                 # Base & home
│   │   ├── auth/                 # Login/register
│   │   ├── contractor/           # Contractor views
│   │   ├── customer/             # Customer views
│   │   ├── search/               # Search results
│   │   └── trust/                # Trust forms
│   ├── static/                   # Static assets
│   │   ├── css/custom.css
│   │   └── js/                   # UI scripts
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend container
│   └── manage.py                 # Django CLI
├── docker-compose.yml            # Multi-container orchestration
└── README.md                     # This file
```

## 🗄️ Database Schema

### Core Models

**User** (Custom)
- email (unique)
- username
- user_type (customer/contractor)
- location (PostGIS Point)
- reviewer_weight

**ContractorProfile**
- user (OneToOne → User)
- office_location (PostGIS Point with GIST index)
- office_address
- service_radius_km
- business_name
- verification_status
- years_in_business

**ServiceCategory & ServiceSubcategory**
- Hierarchical taxonomy
- is_active flag

**ContractorService**
- contractor (FK → ContractorProfile)
- category (FK → ServiceCategory)
- subcategories (M2M → ServiceSubcategory)
- title, description
- trust_score (calculated)
- pricing_model

**TrustMark**
- customer (FK → User)
- service (FK → ContractorService)
- trust_level (1-5)
- status (pending/verified/flagged)
- Unique constraint: (customer, service)

**Review**
- trust_mark (OneToOne → TrustMark)
- rating, title, description
- is_verified

**ReviewHelpfulness**
- review (FK → Review)
- customer (FK → User)
- is_helpful (boolean)

## 🔧 Configuration

### Django Settings
- Session-based authentication (no JWT)
- Redis cache backend (`django-redis`)
- PostGIS database backend
- Cache timeout: 60s (search), 120s (detail pages)

### Docker Services
- **backend**: Django app on port 8000
- **db**: PostgreSQL 15 + PostGIS 3.3 on port 5432
- **redis**: Redis 7 on port 6379

### Environment Variables
```env
# Database
DATABASE_NAME=localkonnect_db
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
DATABASE_HOST=db

# Redis
REDIS_URL=redis://localkonnect_redis:6379/1

# Django
SECRET_KEY=<auto-generated>
DEBUG=True
```

## 🧪 Development & Testing

### Running Tests
```powershell
# Run all Django tests
docker compose exec backend python manage.py test

# Run specific app tests
docker compose exec backend python manage.py test apps.users
docker compose exec backend python manage.py test apps.contractors
docker compose exec backend python manage.py test apps.trust

# Check for issues
docker compose exec backend python manage.py check
```

### Database Management
```powershell
# Create new migrations
docker compose exec backend python manage.py makemigrations

# Apply migrations
docker compose exec backend python manage.py migrate

# Access Django shell
docker compose exec backend python manage.py shell

# Access PostgreSQL
docker compose exec db psql -U postgres -d localkonnect_db
```

### Viewing Application URLs
```powershell
docker compose exec backend python manage.py show_urls
```

## 📚 Key Features Explained

### Geospatial Search
LocalKonnect uses PostGIS for powerful location-based queries. The system can:
- Find contractors within a specified radius
- Calculate distances between locations
- Optimize searches using GIST spatial indexes
- Cache frequent search results for better performance

### Trust System
The platform implements a comprehensive trust and reputation system:
- Customers can mark services they trust
- Each trust mark is unique per customer-service pair
- Reviews are linked to trust marks for authenticity
- Community-driven review helpfulness voting

### Security Features
- Session-based authentication with secure cookies
- Redis-backed rate limiting to prevent abuse
- CSRF protection on all forms
- Role-based access control for contractor features

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request



A full-stack Django application demonstrating:
- Advanced geospatial features with PostGIS
- Scalable caching strategies with Redis
- Modern Docker-based deployment
- Trust and reputation system architecture
- Clean, maintainable code structure

---

**Version:** 1.0.0
```bash
# Backend linting
cd backend
flake8 .
black .

# Frontend linting
cd frontend
npm run lint
npm run format
```

## Deployment

### Docker Deployment
```bash
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment
1. Set up PostgreSQL with PostGIS extension
2. Configure environment variables for production
3. Collect static files: `python manage.py collectstatic`
4. Run migrations: `python manage.py migrate`
5. Start Gunicorn: `gunicorn config.wsgi:application`
6. Start Celery workers and beat scheduler
7. Build frontend: `npm run build`
8. Serve with Nginx

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Acknowledgments

- Google Gemini AI for intelligent features
- PostGIS for geospatial capabilities
- The Django and React communities
