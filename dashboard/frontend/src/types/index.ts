export enum DamageLevel {
  SAFE = "safe",
  DAMAGED = "damaged",
  COLLAPSED = "collapsed"
}

export enum DetectionStatus {
  CONFIRMED = "confirmed",
  POTENTIAL = "potential",
  FALSE_POSITIVE = "false_positive"
}

export interface Coordinates {
  latitude: number;
  longitude: number;
}

export interface BoundingBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
  confidence: number;
}

export interface SurvivorDetection {
  id: string;
  bbox: BoundingBox;
  confidence: number;
  status: DetectionStatus;
  timestamp: string;
  coordinates: Coordinates;
}

export interface BuildingDamage {
  id: string;
  coordinates: Coordinates;
  damage_level: DamageLevel;
  confidence: number;
  area_sqm: number;
  timestamp: string;
}

export interface SegmentationMask {
  mask_url: string;
  safe_percentage: number;
  damaged_percentage: number;
  collapsed_percentage: number;
}

export interface DroneFlightData {
  flight_id: string;
  drone_id: string;
  timestamp: string;
  coordinates: Coordinates;
  altitude: number;
  image_url: string;
  segmentation_mask?: SegmentationMask;
  building_damages: BuildingDamage[];
  survivor_detections: SurvivorDetection[];
  processing_status: string;
}

export interface DisasterZone {
  zone_id: string;
  name: string;
  center_coordinates: Coordinates;
  boundary_polygon: Coordinates[];
  severity_level: number;
  total_buildings: number;
  safe_buildings: number;
  damaged_buildings: number;
  collapsed_buildings: number;
  survivor_count: number;
  last_updated: string;
}

export interface AnalyticsSummary {
  total_flights: number;
  total_area_covered_sqkm: number;
  total_buildings_assessed: number;
  total_survivors_detected: number;
  damage_distribution: Record<string, number>;
  recent_activity: DroneFlightData[];
  active_zones: DisasterZone[];
}

export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
} 