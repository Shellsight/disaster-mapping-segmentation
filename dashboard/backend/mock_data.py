from datetime import datetime, timedelta
from typing import List
import random
from models import *

# Myanmar earthquake region coordinates (roughly around affected areas)
MYANMAR_REGION = {
    "center": {"lat": 22.0, "lng": 96.0},
    "bounds": {
        "north": 22.5,
        "south": 21.5,
        "east": 96.5,
        "west": 95.5
    }
}

def generate_random_coordinate_in_region() -> Coordinates:
    """Generate random coordinates within Myanmar affected region"""
    lat = random.uniform(MYANMAR_REGION["bounds"]["south"], MYANMAR_REGION["bounds"]["north"])
    lng = random.uniform(MYANMAR_REGION["bounds"]["west"], MYANMAR_REGION["bounds"]["east"])
    return Coordinates(latitude=lat, longitude=lng)

def generate_disaster_zones() -> List[DisasterZone]:
    """Generate mock disaster zones"""
    zones = []
    zone_names = [
        "Mandalay Urban Center",
        "Sagaing Rural District", 
        "Myitkyina Township",
        "Lashio Commercial Area",
        "Monywa Residential Zone",
        "Shwebo Agricultural District"
    ]
    
    for i, name in enumerate(zone_names):
        center = generate_random_coordinate_in_region()
        
        # Create boundary polygon (roughly rectangular around center)
        boundary = [
            Coordinates(latitude=center.latitude - 0.02, longitude=center.longitude - 0.02),
            Coordinates(latitude=center.latitude - 0.02, longitude=center.longitude + 0.02),
            Coordinates(latitude=center.latitude + 0.02, longitude=center.longitude + 0.02),
            Coordinates(latitude=center.latitude + 0.02, longitude=center.longitude - 0.02),
        ]
        
        total_buildings = random.randint(50, 300)
        collapsed = random.randint(5, total_buildings // 4)
        damaged = random.randint(10, total_buildings // 3)
        safe = total_buildings - collapsed - damaged
        
        zones.append(DisasterZone(
            zone_id=f"zone_{i+1}",
            name=name,
            center_coordinates=center,
            boundary_polygon=boundary,
            severity_level=random.randint(2, 5),
            total_buildings=total_buildings,
            safe_buildings=safe,
            damaged_buildings=damaged,
            collapsed_buildings=collapsed,
            survivor_count=random.randint(0, 15),
            last_updated=datetime.now() - timedelta(minutes=random.randint(1, 60))
        ))
    
    return zones

def generate_building_damages(num_buildings: int = 50) -> List[BuildingDamage]:
    """Generate mock building damage assessments"""
    damages = []
    damage_levels = [DamageLevel.SAFE, DamageLevel.DAMAGED, DamageLevel.COLLAPSED]
    
    for i in range(num_buildings):
        # Weight damage levels to simulate realistic disaster scenario
        weights = [0.5, 0.35, 0.15]  # 50% safe, 35% damaged, 15% collapsed
        damage_level = random.choices(damage_levels, weights=weights)[0]
        
        damages.append(BuildingDamage(
            id=f"building_{i+1}",
            coordinates=generate_random_coordinate_in_region(),
            damage_level=damage_level,
            confidence=random.uniform(0.7, 0.98),
            area_sqm=random.uniform(50, 500),
            timestamp=datetime.now() - timedelta(minutes=random.randint(1, 120))
        ))
    
    return damages

def generate_survivor_detections(num_detections: int = 25) -> List[SurvivorDetection]:
    """Generate mock survivor detections"""
    detections = []
    statuses = [DetectionStatus.CONFIRMED, DetectionStatus.POTENTIAL, DetectionStatus.FALSE_POSITIVE]
    
    for i in range(num_detections):
        # Weight detection statuses
        weights = [0.4, 0.45, 0.15]  # 40% confirmed, 45% potential, 15% false positive
        status = random.choices(statuses, weights=weights)[0]
        
        detections.append(SurvivorDetection(
            id=f"survivor_{i+1}",
            bbox=BoundingBox(
                x1=random.uniform(0.1, 0.6),
                y1=random.uniform(0.1, 0.6),
                x2=random.uniform(0.4, 0.9),
                y2=random.uniform(0.4, 0.9),
                confidence=random.uniform(0.6, 0.95)
            ),
            confidence=random.uniform(0.6, 0.95),
            status=status,
            timestamp=datetime.now() - timedelta(minutes=random.randint(1, 180)),
            coordinates=generate_random_coordinate_in_region()
        ))
    
    return detections

def generate_drone_flights(num_flights: int = 20) -> List[DroneFlightData]:
    """Generate mock drone flight data"""
    flights = []
    drone_ids = ["DRONE_001", "DRONE_002", "DRONE_003", "DRONE_004", "DRONE_005"]
    
    for i in range(num_flights):
        # Generate some buildings and survivors for each flight
        num_buildings = random.randint(3, 12)
        num_survivors = random.randint(0, 5)
        
        flight = DroneFlightData(
            flight_id=f"flight_{i+1:03d}",
            drone_id=random.choice(drone_ids),
            timestamp=datetime.now() - timedelta(minutes=random.randint(1, 240)),
            coordinates=generate_random_coordinate_in_region(),
            altitude=random.uniform(50, 150),
            image_url=f"https://storage.googleapis.com/disaster-images/flight_{i+1:03d}.jpg",
            segmentation_mask=SegmentationMask(
                mask_url=f"https://storage.googleapis.com/disaster-masks/mask_{i+1:03d}.png",
                safe_percentage=random.uniform(40, 70),
                damaged_percentage=random.uniform(20, 40),
                collapsed_percentage=random.uniform(5, 20)
            ),
            building_damages=generate_building_damages(num_buildings),
            survivor_detections=generate_survivor_detections(num_survivors),
            processing_status="completed"
        )
        flights.append(flight)
    
    return flights

def get_analytics_summary() -> AnalyticsSummary:
    """Generate analytics summary with current mock data"""
    zones = generate_disaster_zones()
    flights = generate_drone_flights(15)
    
    total_buildings = sum(zone.total_buildings for zone in zones)
    total_survivors = sum(zone.survivor_count for zone in zones)
    
    damage_distribution = {
        "safe": sum(zone.safe_buildings for zone in zones),
        "damaged": sum(zone.damaged_buildings for zone in zones),
        "collapsed": sum(zone.collapsed_buildings for zone in zones)
    }
    
    return AnalyticsSummary(
        total_flights=len(flights),
        total_area_covered_sqkm=round(random.uniform(15, 45), 2),
        total_buildings_assessed=total_buildings,
        total_survivors_detected=total_survivors,
        damage_distribution=damage_distribution,
        recent_activity=flights[:5],  # Last 5 flights
        active_zones=zones
    )

# Generate static mock data
MOCK_ZONES = generate_disaster_zones()
MOCK_FLIGHTS = generate_drone_flights(30)
MOCK_BUILDINGS = generate_building_damages(100)
MOCK_SURVIVORS = generate_survivor_detections(40) 