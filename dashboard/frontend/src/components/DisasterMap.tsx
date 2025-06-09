import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polygon } from 'react-leaflet';
import { Icon, LatLngExpression } from 'leaflet';
import { Spin, Tag } from 'antd';
import { 
  DisasterZone, 
  BuildingDamage, 
  SurvivorDetection, 
  DamageLevel, 
  DetectionStatus,
  Coordinates 
} from '../types';
import dayjs from 'dayjs';

// Custom marker icons
const createIcon = (color: string) => new Icon({
  iconUrl: `data:image/svg+xml;base64,${btoa(`
    <svg width="25" height="25" viewBox="0 0 25 25" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12.5" cy="12.5" r="10" fill="${color}" stroke="#ffffff" stroke-width="2"/>
    </svg>
  `)}`,
  iconSize: [25, 25],
  iconAnchor: [12.5, 12.5],
  popupAnchor: [0, -12.5],
});

// Icon configurations
const icons = {
  safe: createIcon('#52c41a'),      // Green
  damaged: createIcon('#faad14'),    // Orange  
  collapsed: createIcon('#ff4d4f'),  // Red
  survivor_confirmed: createIcon('#1890ff'),   // Blue
  survivor_potential: createIcon('#faad14'),   // Orange
  survivor_false: createIcon('#d9d9d9'),       // Gray
};

interface DisasterMapProps {
  zones: DisasterZone[];
  buildings: BuildingDamage[];
  survivors: SurvivorDetection[];
  selectedZone?: string;
  loading?: boolean;
  onZoneClick?: (zone: DisasterZone) => void;
}

const DisasterMap: React.FC<DisasterMapProps> = ({
  zones,
  buildings,
  survivors,
  selectedZone,
  loading = false,
  onZoneClick,
}) => {
  const [mapCenter, setMapCenter] = useState<LatLngExpression>([22.0, 96.0]);
  const [mapZoom, setMapZoom] = useState(10);

  const getDamageColor = (level: DamageLevel): string => {
    switch (level) {
      case DamageLevel.SAFE: return '#52c41a';
      case DamageLevel.DAMAGED: return '#faad14';
      case DamageLevel.COLLAPSED: return '#ff4d4f';
      default: return '#d9d9d9';
    }
  };

  const getSurvivorIcon = (status: DetectionStatus) => {
    switch (status) {
      case DetectionStatus.CONFIRMED: return icons.survivor_confirmed;
      case DetectionStatus.POTENTIAL: return icons.survivor_potential;
      case DetectionStatus.FALSE_POSITIVE: return icons.survivor_false;
      default: return icons.survivor_potential;
    }
  };

  const convertToLatLng = (coords: Coordinates): LatLngExpression => [
    coords.latitude, coords.longitude
  ];

  if (loading) {
    return (
      <div style={{ height: '100%', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        <Spin size="large" tip="Loading map data..." />
      </div>
    );
  }

  return (
    <div style={{ height: '100%', width: '100%', position: 'relative' }}>
      <MapContainer
        center={mapCenter}
        zoom={mapZoom}
        style={{ height: '100%', width: '100%' }}
        scrollWheelZoom={true}
      >
        <TileLayer
          attribution='&copy; OpenStreetMap contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Disaster zones */}
        {zones.map((zone) => (
          <Polygon
            key={zone.zone_id}
            positions={zone.boundary_polygon.map(convertToLatLng)}
            pathOptions={{
              color: zone.severity_level >= 4 ? '#ff4d4f' : '#faad14',
              weight: 2,
              opacity: 0.8,
              fillOpacity: 0.2,
            }}
            eventHandlers={{
              click: () => onZoneClick?.(zone),
            }}
          >
            <Popup>
              <div>
                <h4>{zone.name}</h4>
                <p>Severity: {zone.severity_level}</p>
                <p>Buildings: {zone.total_buildings}</p>
                <p>Survivors: {zone.survivor_count}</p>
              </div>
            </Popup>
          </Polygon>
        ))}

        {/* Buildings */}
        {buildings.map((building) => (
          <Marker
            key={building.id}
            position={convertToLatLng(building.coordinates)}
            icon={icons[building.damage_level]}
          >
            <Popup>
              <div>
                <h4>Building {building.id}</h4>
                <Tag color={getDamageColor(building.damage_level)}>
                  {building.damage_level.toUpperCase()}
                </Tag>
                <p>Confidence: {Math.round(building.confidence * 100)}%</p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Survivors */}
        {survivors.map((survivor) => (
          <Marker
            key={survivor.id}
            position={convertToLatLng(survivor.coordinates)}
            icon={getSurvivorIcon(survivor.status)}
          >
            <Popup>
              <div>
                <h4>Survivor Detection</h4>
                <p>Status: {survivor.status}</p>
                <p>Confidence: {Math.round(survivor.confidence * 100)}%</p>
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
};

export default DisasterMap; 