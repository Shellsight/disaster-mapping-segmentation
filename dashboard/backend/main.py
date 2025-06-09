from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Optional
import asyncio
import json
from datetime import datetime
import random

from models import *
from mock_data import (
    MOCK_ZONES, MOCK_FLIGHTS, MOCK_BUILDINGS, MOCK_SURVIVORS,
    get_analytics_summary, generate_drone_flights
)

app = FastAPI(
    title="Disaster Response Dashboard API",
    description="Real-time API for disaster response visualization and monitoring",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove broken connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.now()}

# Analytics endpoints
@app.get("/api/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics():
    """Get overall analytics summary"""
    return get_analytics_summary()

# Zone endpoints
@app.get("/api/zones", response_model=List[DisasterZone])
async def get_disaster_zones():
    """Get all disaster zones"""
    return MOCK_ZONES

@app.get("/api/zones/{zone_id}", response_model=DisasterZone)
async def get_zone_detail(zone_id: str):
    """Get detailed information about a specific zone"""
    zone = next((z for z in MOCK_ZONES if z.zone_id == zone_id), None)
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")
    return zone

# Flight endpoints
@app.get("/api/flights", response_model=List[DroneFlightData])
async def get_drone_flights(limit: Optional[int] = 20, zone_id: Optional[str] = None):
    """Get drone flight data with optional filtering"""
    flights = MOCK_FLIGHTS[:limit] if limit else MOCK_FLIGHTS
    
    if zone_id:
        # Filter flights by zone (simplified - in real app would check coordinate bounds)
        zone = next((z for z in MOCK_ZONES if z.zone_id == zone_id), None)
        if zone:
            # Return flights within roughly same area as zone
            filtered_flights = []
            for flight in flights:
                if (abs(flight.coordinates.latitude - zone.center_coordinates.latitude) < 0.05 and
                    abs(flight.coordinates.longitude - zone.center_coordinates.longitude) < 0.05):
                    filtered_flights.append(flight)
            flights = filtered_flights
    
    return flights

@app.get("/api/flights/{flight_id}", response_model=DroneFlightData)
async def get_flight_detail(flight_id: str):
    """Get detailed information about a specific flight"""
    flight = next((f for f in MOCK_FLIGHTS if f.flight_id == flight_id), None)
    if not flight:
        raise HTTPException(status_code=404, detail="Flight not found")
    return flight

# Building damage endpoints
@app.get("/api/buildings", response_model=List[BuildingDamage])
async def get_building_damages(
    damage_level: Optional[DamageLevel] = None,
    zone_id: Optional[str] = None,
    limit: Optional[int] = 100
):
    """Get building damage assessments with optional filtering"""
    buildings = MOCK_BUILDINGS[:limit] if limit else MOCK_BUILDINGS
    
    if damage_level:
        buildings = [b for b in buildings if b.damage_level == damage_level]
    
    if zone_id:
        zone = next((z for z in MOCK_ZONES if z.zone_id == zone_id), None)
        if zone:
            filtered_buildings = []
            for building in buildings:
                if (abs(building.coordinates.latitude - zone.center_coordinates.latitude) < 0.05 and
                    abs(building.coordinates.longitude - zone.center_coordinates.longitude) < 0.05):
                    filtered_buildings.append(building)
            buildings = filtered_buildings
    
    return buildings

# Survivor detection endpoints
@app.get("/api/survivors", response_model=List[SurvivorDetection])
async def get_survivor_detections(
    status: Optional[DetectionStatus] = None,
    zone_id: Optional[str] = None,
    limit: Optional[int] = 50
):
    """Get survivor detection data with optional filtering"""
    survivors = MOCK_SURVIVORS[:limit] if limit else MOCK_SURVIVORS
    
    if status:
        survivors = [s for s in survivors if s.status == status]
    
    if zone_id:
        zone = next((z for z in MOCK_ZONES if z.zone_id == zone_id), None)
        if zone:
            filtered_survivors = []
            for survivor in survivors:
                if (abs(survivor.coordinates.latitude - zone.center_coordinates.latitude) < 0.05 and
                    abs(survivor.coordinates.longitude - zone.center_coordinates.longitude) < 0.05):
                    filtered_survivors.append(survivor)
            survivors = filtered_survivors
    
    return survivors

# Real-time data simulation endpoints
@app.post("/api/simulate/new-flight")
async def simulate_new_flight():
    """Simulate a new drone flight for testing real-time updates"""
    new_flights = generate_drone_flights(1)
    new_flight = new_flights[0]
    
    # Add to mock data
    MOCK_FLIGHTS.append(new_flight)
    
    # Broadcast to WebSocket clients
    message = WebSocketMessage(
        type="flight_update",
        data=new_flight.dict(),
        timestamp=datetime.now()
    )
    
    await manager.broadcast(message.json())
    
    return {"message": "New flight simulated", "flight": new_flight}

@app.post("/api/simulate/survivor-detection")
async def simulate_survivor_detection():
    """Simulate a new survivor detection for testing"""
    from mock_data import generate_survivor_detections
    
    new_survivors = generate_survivor_detections(1)
    new_survivor = new_survivors[0]
    
    # Add to mock data
    MOCK_SURVIVORS.append(new_survivor)
    
    # Broadcast to WebSocket clients
    message = WebSocketMessage(
        type="new_detection",
        data=new_survivor.dict(),
        timestamp=datetime.now()
    )
    
    await manager.broadcast(message.json())
    
    return {"message": "New survivor detection simulated", "survivor": new_survivor}

# WebSocket endpoint for real-time updates
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Send periodic updates (every 30 seconds)
            await asyncio.sleep(30)
            
            # Send random update
            update_type = random.choice(["zone_update", "flight_update"])
            
            if update_type == "zone_update":
                zone = random.choice(MOCK_ZONES)
                message = WebSocketMessage(
                    type="zone_update",
                    data=zone.dict(),
                    timestamp=datetime.now()
                )
            else:
                flight = random.choice(MOCK_FLIGHTS[-5:])  # Recent flights
                message = WebSocketMessage(
                    type="flight_update",
                    data=flight.dict(),
                    timestamp=datetime.now()
                )
            
            await manager.send_personal_message(message.json(), websocket)
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Disaster Response Dashboard API",
        "version": "1.0.0",
        "docs_url": "/docs",
        "websocket_url": "/ws"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 