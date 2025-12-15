#!/usr/bin/env pwsh
# LocalKonnect Setup Script for Windows PowerShell
# This script sets up the development environment for LocalKonnect

Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "LocalKonnect Setup Script" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
Write-Host "Checking Docker installation..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker is installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker is not installed. Please install Docker Desktop." -ForegroundColor Red
    Write-Host "Download from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

# Check if Docker Compose is available
Write-Host "Checking Docker Compose..." -ForegroundColor Yellow
try {
    $composeVersion = docker-compose --version
    Write-Host "✓ Docker Compose is available: $composeVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker Compose is not available." -ForegroundColor Red
    exit 1
}

# Create .env file if it doesn't exist
if (-not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "Creating .env file from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✓ .env file created" -ForegroundColor Green
    Write-Host ""
    Write-Host "⚠ Please edit .env file and add your:" -ForegroundColor Yellow
    Write-Host "  - GEMINI_API_KEY (get from https://ai.google.dev/)" -ForegroundColor Yellow
    Write-Host "  - Email credentials (if using email features)" -ForegroundColor Yellow
    Write-Host "  - Other configuration as needed" -ForegroundColor Yellow
    Write-Host ""
    
    $continue = Read-Host "Have you configured your .env file? (y/n)"
    if ($continue -ne "y") {
        Write-Host "Please configure .env and run this script again." -ForegroundColor Yellow
        exit 0
    }
} else {
    Write-Host "✓ .env file exists" -ForegroundColor Green
}

Write-Host ""
Write-Host "Building Docker containers..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker containers built successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to build Docker containers" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Starting Docker containers..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Docker containers started successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to start Docker containers" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Waiting for database to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "Running database migrations..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py migrate

if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Migrations completed successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Failed to run migrations" -ForegroundColor Red
    Write-Host "You may need to run migrations manually:" -ForegroundColor Yellow
    Write-Host "  docker-compose exec backend python manage.py migrate" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Loading initial data (service categories)..." -ForegroundColor Yellow
docker-compose exec -T backend python manage.py loaddata initial_categories

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Create a superuser (if not already done):" -ForegroundColor White
Write-Host "   docker-compose exec backend python manage.py createsuperuser --username admin --email admin@example.com --user_type admin" -ForegroundColor Gray
Write-Host ""
Write-Host "2. Access the application:" -ForegroundColor White
Write-Host "   Homepage:    http://localhost:8000" -ForegroundColor Gray
Write-Host "   Backend API: http://localhost:8000/api" -ForegroundColor Gray
Write-Host "   Admin Panel: http://localhost:8000/admin" -ForegroundColor Gray
Write-Host "   API Docs:    http://localhost:8000/swagger" -ForegroundColor Gray
Write-Host ""
Write-Host "3. View logs:" -ForegroundColor White
Write-Host "   docker-compose logs -f" -ForegroundColor Gray
Write-Host ""
Write-Host "4. Stop services:" -ForegroundColor White
Write-Host "   docker-compose down" -ForegroundColor Gray
Write-Host ""
Write-Host "Note: Django server runs INSIDE Docker container." -ForegroundColor Yellow
Write-Host "Do NOT run 'python manage.py runserver' separately!" -ForegroundColor Yellow
Write-Host ""
