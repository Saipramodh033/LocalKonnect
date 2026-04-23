# LocalKonnect - Trusted Local Contractor Network

A robust, lean Django-based web platform connecting customers with reliable local contractors through a geospatial search and an automated trust scoring system.

## 🎯 Project Overview

LocalKonnect helps customers find trustworthy local contractors while providing contractors a platform to showcase their services and build their reputation through customer feedback and trust scores. The platform was recently refactored to focus on a highly stable, synchronous core flow: **Customer -> Search -> Contractor Detail -> Submit Feedback -> Trust Score Updates -> Reflected in Search.**

## ✨ Core Features

### User Management
- ✅ Custom user model with role-based access (Customer / Contractor)
- ✅ Standard session-based authentication
- ✅ Google OAuth integration with smart user-type auto-detection
- ✅ User profile management with exact geographical coordinates (PostGIS Point field)
- ✅ Built-in password reset functionality (utilizing Django's secure token system and console email backend)

### Contractor Features
- ✅ Auto-created contractor profiles via Django signals
- ✅ Office location tracking with PostGIS `Point` field and `GIST` indexes
- ✅ Service radius configuration
- ✅ Verification status tracking

### Service Management
- ✅ Service categories and subcategories
- ✅ Contractor service management
- ✅ Per-service trust scores calculated automatically based on customer feedback

### Trust & Feedback System
- ✅ Synchronous `Feedback` model ensuring absolute data integrity
- ✅ 1-5 star rating system with verified feedback bonuses
- ✅ Dynamic trust score algorithm combining rating, verified status, and contractor experience
- ✅ Trust score instantly updates and reflects in search rankings upon feedback submission
- ✅ Public contractor profiles display aggregated, filterable, and paginated review histories
- ✅ **Hyper-local review filtering:** Utilizes PostGIS `DWithin` to automatically badge and filter reviews from customers located within a 25km radius of the viewing user.

### Geospatial Search
- ✅ PostGIS-powered distance-based search
- ✅ Filter contractors by category and location
- ✅ Radius search to match customers with nearby contractors
- ✅ Results deterministically ordered by trust score and distance

### Infrastructure
- ✅ Docker Compose local setup
- ✅ PostgreSQL 15 with PostGIS 3.3
- ✅ Native Django management commands for nightly maintenance tasks (e.g., `python manage.py recompute_trust_scores`)
- ✅ Lean, server-rendered frontend using Django Templates, Tailwind CSS (CDN), and Alpine.js

## 🛠️ Tech Stack

### Backend
- **Django 4.2.8** - Core web framework
- **PostgreSQL 15 + PostGIS 3.3** - Primary database with robust geospatial support

### Frontend (Server-Rendered)
- **Django Templates** - Template engine
- **Tailwind CSS** (CDN) - Utility-first styling
- **Alpine.js** - Lightweight reactive components
- **Vanilla JavaScript** - Map integration (Leaflet.js) and UI logic

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

2. **Start the application:**
```powershell
docker compose up -d --build
```

3. **Run database migrations:**
```powershell
docker compose exec backend python manage.py migrate
```

4. **Seed realistic demo data:**
```powershell
# Create categories first
docker compose exec backend python manage.py create_categories

# Seed 10 contractors, 10 customers, services, and feedback
docker compose exec backend python manage.py seed_realistic_demo_data
```

5. **Create a superuser (optional):**
```powershell
docker compose exec backend python manage.py shell -c "
from apps.users.models import User
User.objects.create_superuser('admin', 'admin@localkonnect.com', 'Admin1234!', user_type='contractor')
"
```

6. **Access the application:**
- **Web Application:** http://localhost:8000
- **Admin Panel:** http://localhost:8000/admin

*Demo Logins:*
- Customer: `customer1@seed.localkonnect.test` / `SeedPass123!`
- Contractor: `contractor1@seed.localkonnect.test` / `SeedPass123!`

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
│   ├── config/                    # Django project settings and root routing
│   ├── apps/
│   │   ├── users/                # User authentication & profiles
│   │   ├── contractors/          # Contractor profiles and signals
│   │   ├── services/             # Service categories and ContractorService models
│   │   ├── trust/                # Feedback models, trust score utilities, and submission logic
│   │   ├── search/               # Geospatial search views and Contractor detail views
│   │   └── customer/             # Minimal customer dashboards
│   ├── templates/                # Django templates (Base, Auth, Contractor, Customer, Search, Trust)
│   ├── static/                   # Static assets (CSS, JS, Images)
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend container configuration
│   └── manage.py                 # Django CLI
├── docker-compose.yml            # Multi-container orchestration (DB and Backend)
└── README.md                     # This file
```

## 🗄️ Database Schema (Core Models)

**User**
- Custom authentication model extending `AbstractUser`
- Handles `user_type` (Customer/Contractor) and PostGIS `location`.

**ContractorProfile**
- One-to-one with `User`.
- Stores `office_location` (PostGIS Point), `service_radius_km`, and business details.

**ServiceCategory & ServiceSubcategory**
- Hierarchical taxonomy for the services offered on the platform.

**ContractorService**
- The core offering linking a Contractor to a ServiceCategory.
- Stores the calculated `trust_score` which is deterministically updated when feedback is given.

**Feedback**
- Links a `Customer` to a `ContractorService`.
- Stores `rating` (1-5), optional text, and `is_verified` status.
- Triggers synchronous trust score recalculation on save.

## 📚 Key Features Explained

### The Trust Score Algorithm
When a customer leaves feedback for a service, the system immediately recalculates the `ContractorService` trust score. The algorithm factors in:
1. **Raw Rating:** The 1-5 star value.
2. **Verification Bonus:** Feedback marked as `is_verified` (e.g. proof of work provided) is weighted significantly heavier.
3. **Reviewer Weight:** Feedback from trusted customers contributes more to the score.
4. **Experience Bonus:** Contractors receive a slight bump based on their `years_of_experience`.
5. **Bayesian Smoothing:** Prevents new services with a single 5-star review from instantly outranking established services with hundreds of solid 4.8-star reviews.

### Geospatial Discovery
LocalKonnect utilizes PostgreSQL's PostGIS extension to handle all location data. When a customer searches:
- It calculates the exact distance between the customer's coordinate and the contractor's office coordinate.
- It filters out contractors if the customer falls outside their configured `service_radius_km`.
- Search queries utilize `GIST` indexes for highly optimized geographical sorting.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

---

**Version:** 1.0.0
