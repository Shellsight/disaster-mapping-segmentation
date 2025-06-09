import axios from 'axios';
import { io, Socket } from 'socket.io-client';
import {
  AnalyticsSummary,
  DisasterZone,
  DroneFlightData,
  BuildingDamage,
  SurvivorDetection,
  DamageLevel,
  DetectionStatus,
  WebSocketMessage
} from '../types';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8001';
const WS_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8001';

// Create axios instance
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
});

// Add request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// API Methods
export const apiService = {
  // Health check
  async checkHealth() {
    const response = await api.get('/health');
    return response.data;
  },

  // Analytics
  async getAnalyticsSummary(): Promise<AnalyticsSummary> {
    const response = await api.get('/api/analytics/summary');
    return response.data;
  },

  // Disaster zones
  async getDisasterZones(): Promise<DisasterZone[]> {
    const response = await api.get('/api/zones');
    return response.data;
  },

  async getZoneDetail(zoneId: string): Promise<DisasterZone> {
    const response = await api.get(`/api/zones/${zoneId}`);
    return response.data;
  },

  // Drone flights
  async getDroneFlights(params?: {
    limit?: number;
    zone_id?: string;
  }): Promise<DroneFlightData[]> {
    const response = await api.get('/api/flights', { params });
    return response.data;
  },

  async getFlightDetail(flightId: string): Promise<DroneFlightData> {
    const response = await api.get(`/api/flights/${flightId}`);
    return response.data;
  },

  // Building damage
  async getBuildingDamages(params?: {
    damage_level?: DamageLevel;
    zone_id?: string;
    limit?: number;
  }): Promise<BuildingDamage[]> {
    const response = await api.get('/api/buildings', { params });
    return response.data;
  },

  // Survivor detections
  async getSurvivorDetections(params?: {
    status?: DetectionStatus;
    zone_id?: string;
    limit?: number;
  }): Promise<SurvivorDetection[]> {
    const response = await api.get('/api/survivors', { params });
    return response.data;
  },

  // Simulation endpoints for testing
  async simulateNewFlight() {
    const response = await api.post('/api/simulate/new-flight');
    return response.data;
  },

  async simulateSurvivorDetection() {
    const response = await api.post('/api/simulate/survivor-detection');
    return response.data;
  },
};

// WebSocket Service
class WebSocketService {
  private socket: Socket | null = null;
  private callbacks: Map<string, Function[]> = new Map();

  connect() {
    if (this.socket) {
      return;
    }

    this.socket = io(WS_URL, {
      transports: ['websocket'],
      autoConnect: true,
    });

    this.socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    this.socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    this.socket.on('message', (data: string) => {
      try {
        const message: WebSocketMessage = JSON.parse(data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });

    this.socket.on('connect_error', (error) => {
      console.error('WebSocket connection error:', error);
    });
  }

  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
    }
  }

  subscribe(messageType: string, callback: Function) {
    if (!this.callbacks.has(messageType)) {
      this.callbacks.set(messageType, []);
    }
    this.callbacks.get(messageType)?.push(callback);
  }

  unsubscribe(messageType: string, callback: Function) {
    const callbacks = this.callbacks.get(messageType);
    if (callbacks) {
      const index = callbacks.indexOf(callback);
      if (index > -1) {
        callbacks.splice(index, 1);
      }
    }
  }

  private handleMessage(message: WebSocketMessage) {
    const callbacks = this.callbacks.get(message.type);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(message);
        } catch (error) {
          console.error('Error in WebSocket callback:', error);
        }
      });
    }
  }

  // Check if connected
  get isConnected(): boolean {
    return this.socket?.connected || false;
  }
}

// Export WebSocket service instance
export const wsService = new WebSocketService();

export default apiService; 