import React from 'react';
import { Card, Row, Col, Statistic, Progress, Table, Tag } from 'antd';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { AnalyticsSummary, DisasterZone, DroneFlightData } from '../types';
import dayjs from 'dayjs';

interface AnalyticsDashboardProps {
  analytics: AnalyticsSummary;
  loading?: boolean;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ analytics, loading = false }) => {
  // Prepare chart data
  const damageDistributionData = [
    { name: 'Safe', value: analytics.damage_distribution.safe, color: '#52c41a' },
    { name: 'Damaged', value: analytics.damage_distribution.damaged, color: '#faad14' },
    { name: 'Collapsed', value: analytics.damage_distribution.collapsed, color: '#ff4d4f' },
  ];

  const zoneData = analytics.active_zones.map(zone => ({
    name: zone.name,
    total: zone.total_buildings,
    safe: zone.safe_buildings,
    damaged: zone.damaged_buildings,
    collapsed: zone.collapsed_buildings,
    survivors: zone.survivor_count,
  }));

  // Table columns for recent flights
  const flightColumns = [
    {
      title: 'Flight ID',
      dataIndex: 'flight_id',
      key: 'flight_id',
      render: (text: string) => <span style={{ fontFamily: 'monospace' }}>{text}</span>,
    },
    {
      title: 'Drone',
      dataIndex: 'drone_id',
      key: 'drone_id',
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      key: 'timestamp',
      render: (text: string) => dayjs(text).format('MMM D, HH:mm'),
    },
    {
      title: 'Altitude',
      dataIndex: 'altitude',
      key: 'altitude',
      render: (value: number) => `${Math.round(value)}m`,
    },
    {
      title: 'Status',
      dataIndex: 'processing_status',
      key: 'processing_status',
      render: (status: string) => (
        <Tag color={status === 'completed' ? 'green' : status === 'processing' ? 'orange' : 'red'}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Detections',
      key: 'detections',
      render: (record: DroneFlightData) => (
        <span>
          {record.building_damages.length} buildings, {record.survivor_detections.length} survivors
        </span>
      ),
    },
  ];

  const totalBuildings = analytics.total_buildings_assessed;
  const safePercentage = totalBuildings > 0 ? (analytics.damage_distribution.safe / totalBuildings) * 100 : 0;
  const damagedPercentage = totalBuildings > 0 ? (analytics.damage_distribution.damaged / totalBuildings) * 100 : 0;
  const collapsedPercentage = totalBuildings > 0 ? (analytics.damage_distribution.collapsed / totalBuildings) * 100 : 0;

  return (
    <div style={{ padding: '24px' }}>
      {/* Key Metrics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Total Flights"
              value={analytics.total_flights}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Area Covered"
              value={analytics.total_area_covered_sqkm}
              suffix="km²"
              valueStyle={{ color: '#52c41a' }}
              precision={1}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Buildings Assessed"
              value={analytics.total_buildings_assessed}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} md={6}>
          <Card>
            <Statistic
              title="Survivors Detected"
              value={analytics.total_survivors_detected}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts and Detailed Analytics */}
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        {/* Damage Distribution Pie Chart */}
        <Col xs={24} lg={12}>
          <Card title="Building Damage Distribution" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={damageDistributionData}
                  cx="50%"
                  cy="50%"
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                >
                  {damageDistributionData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
            
            {/* Progress bars */}
            <div style={{ marginTop: '16px' }}>
              <div style={{ marginBottom: '8px' }}>
                <span>Safe Buildings: </span>
                <Progress 
                  percent={safePercentage} 
                  strokeColor="#52c41a" 
                  format={() => `${analytics.damage_distribution.safe}`}
                />
              </div>
              <div style={{ marginBottom: '8px' }}>
                <span>Damaged Buildings: </span>
                <Progress 
                  percent={damagedPercentage} 
                  strokeColor="#faad14"
                  format={() => `${analytics.damage_distribution.damaged}`}
                />
              </div>
              <div>
                <span>Collapsed Buildings: </span>
                <Progress 
                  percent={collapsedPercentage} 
                  strokeColor="#ff4d4f"
                  format={() => `${analytics.damage_distribution.collapsed}`}
                />
              </div>
            </div>
          </Card>
        </Col>

        {/* Zone Comparison Bar Chart */}
        <Col xs={24} lg={12}>
          <Card title="Zone Assessment Overview" loading={loading}>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={zoneData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="name" 
                  angle={-45}
                  textAnchor="end"
                  height={80}
                  fontSize={10}
                />
                <YAxis />
                <Tooltip />
                <Bar dataKey="safe" stackId="a" fill="#52c41a" name="Safe" />
                <Bar dataKey="damaged" stackId="a" fill="#faad14" name="Damaged" />
                <Bar dataKey="collapsed" stackId="a" fill="#ff4d4f" name="Collapsed" />
              </BarChart>
            </ResponsiveContainer>
          </Card>
        </Col>
      </Row>

      {/* Recent Activity Table */}
      <Card title="Recent Flight Activity" loading={loading}>
        <Table
          columns={flightColumns}
          dataSource={analytics.recent_activity}
          rowKey="flight_id"
          pagination={{ pageSize: 10 }}
          scroll={{ x: 'max-content' }}
        />
      </Card>

      {/* Zone Status Cards */}
      <Card title="Active Disaster Zones" style={{ marginTop: '24px' }} loading={loading}>
        <Row gutter={[16, 16]}>
          {analytics.active_zones.map((zone) => (
            <Col xs={24} sm={12} lg={8} key={zone.zone_id}>
              <Card 
                size="small"
                title={zone.name}
                extra={
                  <Tag color={zone.severity_level >= 4 ? 'red' : zone.severity_level >= 3 ? 'orange' : 'yellow'}>
                    Level {zone.severity_level}
                  </Tag>
                }
              >
                <Row gutter={[8, 8]}>
                  <Col span={12}>
                    <Statistic
                      title="Total Buildings"
                      value={zone.total_buildings}
                      valueStyle={{ fontSize: '16px' }}
                    />
                  </Col>
                  <Col span={12}>
                    <Statistic
                      title="Survivors"
                      value={zone.survivor_count}
                      valueStyle={{ fontSize: '16px', color: '#ff4d4f' }}
                    />
                  </Col>
                </Row>
                <div style={{ marginTop: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                    <span style={{ fontSize: '12px' }}>Safe: {zone.safe_buildings}</span>
                    <span style={{ fontSize: '12px' }}>Damaged: {zone.damaged_buildings}</span>
                    <span style={{ fontSize: '12px' }}>Collapsed: {zone.collapsed_buildings}</span>
                  </div>
                  <Progress
                    percent={100}
                    success={{ percent: (zone.safe_buildings / zone.total_buildings) * 100 }}
                    strokeColor="#ff4d4f"
                    showInfo={false}
                    size="small"
                  />
                </div>
                <p style={{ margin: '8px 0 0 0', fontSize: '11px', color: '#666' }}>
                  Last updated: {dayjs(zone.last_updated).format('MMM D, HH:mm')}
                </p>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>
    </div>
  );
};

export default AnalyticsDashboard; 