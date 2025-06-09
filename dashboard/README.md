# Disaster Response Dashboard

## Overview
A real-time web dashboard for visualizing disaster response data including building damage assessment and survivor detection from UAV/drone imagery.

## Features
- **Interactive Map**: Real-time visualization of disaster zones
- **Building Damage Classification**: Visual overlay showing Safe, Damaged, and Collapsed structures
- **Survivor Detection**: Markers indicating potential survivor locations
- **Real-time Updates**: WebSocket connection for live data streaming
- **Analytics Dashboard**: Summary statistics and trends
- **Responsive Design**: Mobile-friendly interface for field operations

## Technology Stack
- **Frontend**: React.js with TypeScript
- **Backend**: FastAPI with Python
- **Map Visualization**: Leaflet.js
- **Real-time Communication**: WebSockets
- **UI Components**: Material-UI / Ant Design
- **Charts**: Chart.js / Recharts

## Directory Structure
```
dashboard/
├── frontend/          # React frontend application
├── backend/           # FastAPI backend service
├── shared/           # Shared utilities and types
├── docker-compose.yml # Development environment
└── README.md         # This file
```

## Quick Start
1. Navigate to dashboard directory: `cd dashboard`
2. Start all services: `docker-compose up -d`
3. Access dashboard: http://localhost:3000
4. API documentation: http://localhost:8001/docs

## Mock Data
The dashboard includes hardcoded sample data representing:
- Myanmar earthquake damage assessment
- Multiple drone flight zones
- Building damage classifications
- Survivor detection results
- Historical trend data 