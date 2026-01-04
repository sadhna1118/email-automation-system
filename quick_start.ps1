# Quick Start Script for Email Automation System
# This script helps you set up and run the project

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Email Automation & Notification System" -ForegroundColor Cyan
Write-Host "Quick Start Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host $pythonVersion -ForegroundColor Green

# Install dependencies
Write-Host ""
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Check if .env exists
if (-Not (Test-Path ".env")) {
    Write-Host ""
    Write-Host "WARNING: .env file not found!" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item .env.example .env
    
    Write-Host ""
    Write-Host "IMPORTANT: Please edit .env file with your email credentials!" -ForegroundColor Red
    Write-Host "For Gmail users:" -ForegroundColor Yellow
    Write-Host "1. Go to https://myaccount.google.com/apppasswords" -ForegroundColor White
    Write-Host "2. Generate an App Password" -ForegroundColor White
    Write-Host "3. Update EMAIL_ADDRESS and EMAIL_PASSWORD in .env" -ForegroundColor White
    Write-Host ""
    
    $response = Read-Host "Have you configured .env with your credentials? (y/n)"
    if ($response -ne "y") {
        Write-Host "Please configure .env file first, then run this script again." -ForegroundColor Yellow
        exit
    }
}

# Run tests
Write-Host ""
Write-Host "Running tests..." -ForegroundColor Yellow
pytest test_email_system.py -v

# Check if tests passed
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "All tests passed! ✓" -ForegroundColor Green
    Write-Host ""
    
    $response = Read-Host "Do you want to start the application now? (y/n)"
    if ($response -eq "y") {
        Write-Host ""
        Write-Host "Starting Email Automation System..." -ForegroundColor Cyan
        python main.py
    } else {
        Write-Host ""
        Write-Host "Setup complete! Run 'python main.py' to start the application." -ForegroundColor Green
    }
} else {
    Write-Host ""
    Write-Host "Tests failed. Please check the configuration." -ForegroundColor Red
    Write-Host "Make sure .env file has correct email credentials." -ForegroundColor Yellow
}