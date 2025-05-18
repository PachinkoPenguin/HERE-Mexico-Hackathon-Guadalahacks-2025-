import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from 'recharts';

const StatsOverview = () => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);

  // Define colors for pie chart
  const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8', 
                 '#82CA9D', '#FF6B6B', '#6A8EEA', '#B678F7', '#5B8FF9'];

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        const response = await axios.get('http://localhost:5001/api/poi-stats');
        setStats(response.data.stats);
        setError(null);
      } catch (err) {
        setError(`Error fetching stats: ${err.message}`);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);
  
  // Add function to fetch stats for specific files
  const [poiFiles, setPoiFiles] = useState([]);
  const [streetFiles, setStreetFiles] = useState([]);
  const [selectedPoiFile, setSelectedPoiFile] = useState('');
  const [selectedStreetFile, setSelectedStreetFile] = useState('');
  
  useEffect(() => {
    // Fetch available POI and street files
    const fetchFiles = async () => {
      try {
        const [poiResponse, streetResponse] = await Promise.all([
          axios.get('http://localhost:5001/api/list-poi-files'),
          axios.get('http://localhost:5001/api/list-street-files')
        ]);
        
        setPoiFiles(poiResponse.data.files || []);
        setStreetFiles(streetResponse.data.files || []);
      } catch (err) {
        console.error('Error fetching file lists:', err);
      }
    };
    
    fetchFiles();
  }, []);
  
  const handleFileSelection = async () => {
    try {
      setLoading(true);
      const params = new URLSearchParams();
      
      if (selectedPoiFile) {
        params.append('poi_file', selectedPoiFile);
      }
      
      if (selectedStreetFile) {
        params.append('street_file', selectedStreetFile);
      }
      
      const response = await axios.get(`http://localhost:5001/api/poi-stats?${params.toString()}`);
      setStats(response.data.stats);
      setError(null);
    } catch (err) {
      setError(`Error fetching stats: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="stats-loading">Loading statistics...</div>;
  }

  if (error) {
    return <div className="stats-error">{error}</div>;
  }

  if (!stats) {
    return <div className="stats-empty">No statistics available</div>;
  }

  // Format data for POI types pie chart
  const poiTypesData = stats.poi_types_summary ? 
    stats.poi_types_summary.slice(0, 8).map(type => ({
      name: type.type_name || `Type ${type.type_id}`,
      value: type.count,
      typeId: type.type_id
    })) : [];

  // Format data for POI side distribution
  const poiSideData = [
    { name: 'Left Side (L)', value: stats.poi_by_side?.L || 0 },
    { name: 'Right Side (R)', value: stats.poi_by_side?.R || 0 },
    { name: 'Both Sides (B)', value: stats.poi_by_side?.B || 0 },
    { name: 'Unknown', value: stats.poi_by_side?.Unknown || 0 }
  ];
      return (
    <div className="stats-overview">
      <h3>Dataset Overview</h3>
      
      {/* File Selection Controls */}
      <div className="file-selection">
        <div className="file-selectors">
          <div className="file-selector">
            <label htmlFor="poi-file">POI File:</label>
            <select 
              id="poi-file" 
              value={selectedPoiFile} 
              onChange={(e) => setSelectedPoiFile(e.target.value)}
            >
              <option value="">All POI Files</option>
              {poiFiles.map(file => (
                <option key={file} value={file}>{file}</option>
              ))}
            </select>
          </div>
          
          <div className="file-selector">
            <label htmlFor="street-file">Street File:</label>
            <select 
              id="street-file" 
              value={selectedStreetFile} 
              onChange={(e) => setSelectedStreetFile(e.target.value)}
            >
              <option value="">No Street File</option>
              {streetFiles.map(file => (
                <option key={file} value={file}>{file}</option>
              ))}
            </select>
          </div>
        </div>
        
        <button 
          className="analyze-button" 
          onClick={handleFileSelection}
          disabled={loading}
        >
          {loading ? 'Analyzing...' : 'Analyze Files'}
        </button>
      </div>
      
      <div className="stats-cards">
        <div className="stats-card">
          <div className="stats-card-title">Total POIs</div>
          <div className="stats-card-value">{(stats.total_pois || 0).toLocaleString()}</div>
        </div>
        {stats.streets_total && (
          <div className="stats-card">
            <div className="stats-card-title">Total Streets</div>
            <div className="stats-card-value">{(stats.streets_total || 0).toLocaleString()}</div>
          </div>
        )}
        <div className="stats-card">
          <div className="stats-card-title">POIs with Link ID</div>
          <div className="stats-card-value">{(stats.poi_with_links || 0).toLocaleString()}</div>
        </div>
        <div className="stats-card">
          <div className="stats-card-title">POIs without Link ID</div>
          <div className="stats-card-value">{(stats.poi_without_links || 0).toLocaleString()}</div>
        </div>
      </div>
      
      <div className="stats-charts">
        <div className="stats-chart">
          <h4>POI Types Distribution</h4>
          {poiTypesData.length > 0 ? (
            <div className="chart-container" style={{ height: 300 }}>
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={poiTypesData}
                    cx="50%"
                    cy="50%"
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                    labelLine={false}
                  >
                    {poiTypesData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => value.toLocaleString()} />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="no-data">No POI type data available</div>
          )}
        </div>
        
        <div className="stats-chart">
          <h4>POI Side Distribution</h4>
          <div className="chart-container" style={{ height: 300 }}>
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={poiSideData}
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                  nameKey="name"
                  label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  labelLine={false}
                >
                  <Cell fill="#0088FE" />
                  <Cell fill="#00C49F" />
                  <Cell fill="#FFBB28" />
                  <Cell fill="#FF8042" />
                </Pie>
                <Tooltip formatter={(value) => value.toLocaleString()} />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
      
      <div className="stats-table">
        <h4>Top POI Types</h4>
        {stats.poi_types_summary && stats.poi_types_summary.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th>Type ID</th>
                <th>Type Name</th>
                <th>Count</th>
                <th>Percentage</th>
              </tr>
            </thead>
            <tbody>
              {stats.poi_types_summary.map((type, idx) => (
                <tr key={idx}>
                  <td>{type.type_id}</td>
                  <td>{type.type_name || 'Unknown'}</td>
                  <td>{type.count.toLocaleString()}</td>
                  <td>{type.percentage}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="no-data">No POI type data available</div>
        )}
      </div>
    </div>
  );
};

export default StatsOverview;
