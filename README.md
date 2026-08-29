# AI-Based Procurement Decision Support System

## Project Overview

This project is an AI-Based Procurement Decision Support System developed to support procurement activities through vendor evaluation, risk prediction, procurement transaction management, price trend analysis, and reporting.

The system is designed to help procurement users manage vendor information and make more informed decisions using data analysis and machine learning techniques.

## Key Features

- User authentication and authorization
- Vendor registration and management
- Add, view, edit and manage vendor information
- Procurement transaction recording
- Vendor performance evaluation
- AI-based vendor risk prediction
- Vendor scoring
- Price trend analysis
- Procurement analytics dashboard
- Report generation

## AI and Machine Learning

The system uses a machine learning model to predict vendor risk based on relevant vendor and procurement-related factors.

Vendor risk can be classified into categories such as:

- Low Risk
- Medium Risk
- High Risk

The system also supports vendor evaluation using factors including:

- Price
- Quality
- Delivery Performance
- Reliability
- Complaints

## Technologies Used

### Backend
- Python
- Flask

### Frontend
- HTML
- CSS
- JavaScript

### Database
- MySQL
- phpMyAdmin

### Data Analysis and Machine Learning
- Pandas
- Scikit-learn
- Joblib

### Development Tools
- Visual Studio Code
- XAMPP
- Git
- GitHub

## System Modules

### 1. User Authentication
Provides secure access to authorized system users.

### 2. Vendor Management
Allows users to add, view, edit and manage vendor information.

### 3. Procurement Transactions
Records and manages procurement transactions.

### 4. Vendor Evaluation
Evaluates vendor performance using selected procurement criteria.

### 5. AI Risk Prediction
Uses a trained machine learning model to predict the risk level of vendors.

### 6. Price Trend Analysis
Analyzes procurement prices and identifies price trends to support decision-making.

### 7. Dashboard and Reports
Provides visual analytics and procurement-related reports.

## Project Structure

```text
AI_Procurement_System/
│
├── backend/
│   ├── app.py
│   ├── static/
│   └── templates/
│
├── database/
│   └── import_data.py
│
├── dataset/
│   └── generate_dataset.py
│
├── model/
│   ├── train_model.py
│   ├── predict_risk.py
│   └── risk_model.pkl
│
├── vendor_dataset.csv
│
└── .gitignore
