import React, { useState, useEffect } from 'react';
import { Layout, Menu, Button, notification, Badge, Spin, Alert } from 'antd';
import {
  DashboardOutlined,
  EnvironmentOutlined,
  ReloadOutlined,
  ExperimentOutlined,
  WifiOutlined,
  DisconnectOutlined,
} from '@ant-design/icons';
import DisasterMap from './components/DisasterMap';
import AnalyticsDashboard from './components/AnalyticsDashboard';
import { apiService, wsService } from './services/api';
import {
  AnalyticsSummary,
  DisasterZone,
  BuildingDamage,
  SurvivorDetection,
  WebSocketMessage,
} from './types';
import 'antd/dist/reset.css';

const { Header, Sider, Content } = Layout;

type TabKey = 'map' | 'analytics';

const App: React.FC = () => {
  // State management
  const [activeTab, setActiveTab] = useState<TabKey>('map');
  const [loading, setLoading] = useState(true);
  const [wsConnected, setWsConnected] = useState(false);
  const [selectedZone, setSelectedZone] = useState<string>();
  
  // Data state
  const [analytics, setAnalytics] = useState<AnalyticsSummary | null>(null);
  const [zones, setZones] = useState<DisasterZone[]>([]);
  const [buildings, setBuildings] = useState<BuildingDamage[]>([]);
  const [survivors, setSurvivors] = useState<SurvivorDetection[]>([]);

  // Initialize data and WebSocket connection
  useEffect(() => {
    loadInitialData();
    connectWebSocket();
    
    return () => {
      wsService.disconnect();
    };
  }, []);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      
      // Load all data in parallel
      const [analyticsData, zonesData, buildingsData, survivorsData] = await Promise.all([
        apiService.getAnalyticsSummary(),
        apiService.getDisasterZones(),
        apiService.getBuildingDamages({ limit: 100 }),
        apiService.getSurvivorDetections({ limit: 50 }),
      ]);

      setAnalytics(analyticsData);
      setZones(zonesData);
      setBuildings(buildingsData);
      setSurvivors(survivorsData);
      
    } catch (error) {
      console.error('Error loading initial data:', error);
      notification.error({
        message: 'Data Loading Error',
        description: 'Failed to load initial data. Please try refreshing.',
      });
    } finally {
      setLoading(false);
    }
  };

  const connectWebSocket = () => {
    wsService.connect();
    
    // Handle WebSocket connection status
    const checkConnection = () => {
      setWsConnected(wsService.isConnected);
    };
    
    const connectionInterval = setInterval(checkConnection, 1000);
    
    // Subscribe to real-time updates
    wsService.subscribe('flight_update', handleFlightUpdate);
    wsService.subscribe('new_detection', handleNewDetection);
    wsService.subscribe('zone_update', handleZoneUpdate);
    
    return () => {
      clearInterval(connectionInterval);
      wsService.unsubscribe('flight_update', handleFlightUpdate);
      wsService.unsubscribe('new_detection', handleNewDetection);
      wsService.unsubscribe('zone_update', handleZoneUpdate);
    };
  };

  const handleFlightUpdate = (message: WebSocketMessage) => {
    console.log('New flight update:', message.data);
    notification.info({
      message: 'New Flight Data',
      description: `Flight ${message.data.flight_id} completed processing`,
      placement: 'topRight',
    });
    
    // Refresh data
    loadInitialData();
  };

  const handleNewDetection = (message: WebSocketMessage) => {
    console.log('New survivor detection:', message.data);
    notification.warning({
      message: 'New Survivor Detection',
      description: `Potential survivor detected with ${Math.round(message.data.confidence * 100)}% confidence`,
      placement: 'topRight',
    });
    
    // Add new detection to state
    setSurvivors(prev => [message.data, ...prev]);
  };

  const handleZoneUpdate = (message: WebSocketMessage) => {
    console.log('Zone update:', message.data);
    notification.info({
      message: 'Zone Update',
      description: `Zone ${message.data.name} has been updated`,
      placement: 'topRight',
    });
    
    // Update zone in state
    setZones(prev => prev.map(zone => 
      zone.zone_id === message.data.zone_id ? message.data : zone
    ));
  };

  const handleRefresh = async () => {
    await loadInitialData();
    notification.success({
      message: 'Data Refreshed',
      description: 'Latest data has been loaded successfully',
    });
  };

  const handleSimulateFlight = async () => {
    try {
      await apiService.simulateNewFlight();
      notification.success({
        message: 'Flight Simulated',
        description: 'New flight data has been generated',
      });
    } catch (error) {
      notification.error({
        message: 'Simulation Error',
        description: 'Failed to simulate new flight',
      });
    }
  };

  const handleSimulateSurvivor = async () => {
    try {
      await apiService.simulateSurvivorDetection();
      notification.success({
        message: 'Detection Simulated',
        description: 'New survivor detection has been generated',
      });
    } catch (error) {
      notification.error({
        message: 'Simulation Error',
        description: 'Failed to simulate survivor detection',
      });
    }
  };

  const handleZoneClick = (zone: DisasterZone) => {
    setSelectedZone(zone.zone_id);
    notification.info({
      message: 'Zone Selected',
      description: `Focused on ${zone.name}`,
    });
  };

  const menuItems = [
    {
      key: 'map',
      icon: <EnvironmentOutlined />,
      label: 'Disaster Map',
    },
    {
      key: 'analytics',
      icon: <DashboardOutlined />,
      label: 'Analytics Dashboard',
    },
  ];

  if (loading && !analytics) {
    return (
      <div style={{ 
        height: '100vh', 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        flexDirection: 'column',
        gap: '16px'
      }}>
        <Spin size="large" />
        <div>Loading Disaster Response Dashboard...</div>
      </div>
    );
  }

  return (
    <Layout style={{ height: '100vh' }}>
      <Header style={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        background: '#001529',
        padding: '0 24px'
      }}>
        <div style={{ color: 'white', fontSize: '18px', fontWeight: 'bold' }}>
          🚁 Disaster Response Dashboard
        </div>
        
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {/* WebSocket Status */}
          <Badge 
            status={wsConnected ? 'processing' : 'error'} 
            text={
              <span style={{ color: 'white', fontSize: '12px' }}>
                {wsConnected ? 'Real-time Connected' : 'Disconnected'}
              </span>
            }
          />
          
          {/* Action Buttons */}
          <Button 
            type="primary" 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={loading}
          >
            Refresh
          </Button>
          
          <Button 
            icon={<ExperimentOutlined />} 
            onClick={handleSimulateFlight}
          >
            Simulate Flight
          </Button>
          
          <Button 
            icon={<ExperimentOutlined />} 
            onClick={handleSimulateSurvivor}
          >
            Simulate Detection
          </Button>
        </div>
      </Header>

      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[activeTab]}
            items={menuItems}
            style={{ height: '100%', borderRight: 0 }}
            onClick={({ key }) => setActiveTab(key as TabKey)}
          />
        </Sider>
        
        <Content style={{ background: '#f0f2f5' }}>
          {!wsConnected && (
            <Alert
              message="Real-time Connection Lost"
              description="WebSocket connection is not available. Data may not be up to date."
              type="warning"
              showIcon
              style={{ margin: '16px' }}
            />
          )}
          
          {activeTab === 'map' && (
            <DisasterMap
              zones={zones}
              buildings={buildings}
              survivors={survivors}
              selectedZone={selectedZone}
              loading={loading}
              onZoneClick={handleZoneClick}
            />
          )}
          
          {activeTab === 'analytics' && analytics && (
            <AnalyticsDashboard 
              analytics={analytics} 
              loading={loading}
            />
          )}
        </Content>
      </Layout>
    </Layout>
  );
};

export default App; 