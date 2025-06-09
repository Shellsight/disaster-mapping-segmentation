from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class DamageLevel(str, Enum):
    SAFE = "safe"
    DAMAGED = "damaged"
    COLLAPSED = "collapsed"

class DetectionStatus(str, Enum):
    CONFIRMED = "confirmed"
    POTENTIAL = "potential"
    FALSE_POSITIVE = "false_positive"

class Coordinates(BaseModel):
    latitude: float
    longitude: float

class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float
    confidence: float

class SurvivorDetection(BaseModel):
    id: str
    bbox: BoundingBox
    confidence: float
    status: DetectionStatus
    timestamp: datetime
    coordinates: Coordinates

class BuildingDamage(BaseModel):
    id: str
    coordinates: Coordinates
    damage_level: DamageLevel
    confidence: float
    area_sqm: float
    timestamp: datetime

class SegmentationMask(BaseModel):
    mask_url: str
    safe_percentage: float
    damaged_percentage: float
    collapsed_percentage: float

class DroneFlightData(BaseModel):
    flight_id: str
    drone_id: str
    timestamp: datetime
    coordinates: Coordinates
    altitude: float
    image_url: str
    segmentation_mask: Optional[SegmentationMask] = None
    building_damages: List[BuildingDamage] = []
    survivor_detections: List[SurvivorDetection] = []
    processing_status: str = "completed"

class DisasterZone(BaseModel):
    zone_id: str
    name: str
    center_coordinates: Coordinates
    boundary_polygon: List[Coordinates]
    severity_level: int  # 1-5 scale
    total_buildings: int
    safe_buildings: int
    damaged_buildings: int
    collapsed_buildings: int
    survivor_count: int
    last_updated: datetime

class AnalyticsSummary(BaseModel):
    total_flights: int
    total_area_covered_sqkm: float
    total_buildings_assessed: int
    total_survivors_detected: int
    damage_distribution: Dict[str, int]
    recent_activity: List[DroneFlightData]
    active_zones: List[DisasterZone]

class WebSocketMessage(BaseModel):
    type: str  # "flight_update", "new_detection", "zone_update"
    data: Dict[str, Any]
    timestamp: datetime 