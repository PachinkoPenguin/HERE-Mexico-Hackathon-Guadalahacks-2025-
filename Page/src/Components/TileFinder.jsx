import React, { useState } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Icon } from 'leaflet';

// Default marker icon
const defaultIcon = new Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

const TileFinder = () => {
  const [lat, setLat] = useState(19.3);
  const [lon, setLon] = useState(-99.6);
  const [zoom, setZoom] = useState(16);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [mapCenter, setMapCenter] = useState([19.3, -99.6]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!lat || !lon) {
      setError('Please enter both latitude and longitude');
      return;
    }
    
    try {
      setLoading(true);
      setError('');
      
      const response = await axios.get(`http://localhost:5001/api/get-tiles?lat=${lat}&lon=${lon}&zoom=${zoom}`);
      setResult(response.data);
      
      // Update map center
      setMapCenter([parseFloat(lat), parseFloat(lon)]);
      
      setLoading(false);
    } catch (err) {
      setError('Error calculating tile coordinates: ' + err.message);
      setLoading(false);
    }
  };

  return (
    <div className="tile-finder-container">
      <div className="mb-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-3">Tile Coordinate Finder</h2>
        <p className="text-gray-600">Enter geographic coordinates to calculate the corresponding map tile coordinates.</p>
      </div>
      
      {error && (
        <div className="bg-red-100 border-l-4 border-red-500 text-red-700 p-4 mb-6 rounded">
          <p className="font-medium">Error</p>
          <p>{error}</p>
        </div>
      )}
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div>
          <form onSubmit={handleSubmit} className="bg-gray-50 p-6 rounded-lg shadow-sm border border-gray-200">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">"
              <div className="form-group">
                <label className="block text-gray-700 text-sm font-medium mb-2">Latitude:</label>
                <input 
                  type="number" 
                  step="any"
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
              
              <div className="form-group">
                <label className="block text-gray-700 text-sm font-medium mb-2">Longitude:</label>
                <input 
                  type="number"
                  step="any"
                  value={lon}
                  onChange={(e) => setLon(e.target.value)}
                  required
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>
            
            <div className="form-group mb-6">
              <label className="block text-gray-700 text-sm font-medium mb-2">Zoom Level:</label>
              <select 
                value={zoom} 
                onChange={(e) => setZoom(parseInt(e.target.value))}
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                {[...Array(20).keys()].map(z => (
                  <option key={z} value={z}>{z}</option>
                ))}
              </select>
              <p className="text-xs text-gray-500 mt-1">Higher values give more detailed tiles.</p>
            </div>
            
            <button 
              type="submit" 
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors duration-200 disabled:bg-blue-400"
            >
              {loading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Calculating...
                </span>
              ) : 'Calculate Tile'}
            </button>
          </form>
          
          {result && (
            <div className="result-container mt-6 bg-white p-6 rounded-lg shadow-sm border border-gray-200">
              <h3 className="text-xl font-semibold text-gray-800 mb-4">Tile Coordinates</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm text-gray-500">Tile X</p>
                  <p className="text-xl font-semibold">{result.tile_x}</p>
                </div>
                <div className="bg-gray-50 p-4 rounded-md">
                  <p className="text-sm text-gray-500">Tile Y</p>
                  <p className="text-xl font-semibold">{result.tile_y}</p>
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-md mt-4">
                <p className="text-sm text-gray-500">Zoom Level</p>
                <p className="text-xl font-semibold">{result.zoom}</p>
              </div>
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">Tile URL Format:</p>
                <code className="block bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                  https://tile.openstreetmap.org/&#123;zoom&#125;/&#123;x&#125;/&#123;y&#125;.png
                </code>
              </div>
              <div className="mt-4">
                <p className="text-sm text-gray-600 mb-2">This Tile URL:</p>
                <code className="block bg-gray-100 p-3 rounded text-sm overflow-x-auto">
                  https://tile.openstreetmap.org/{result.zoom}/{result.tile_x}/{result.tile_y}.png
                </code>
              </div>
            </div>
          )}
        </div>
        
        <div className="map-container">
          <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
            <h3 className="text-xl font-semibold text-gray-800 mb-4">Map View</h3>
            <div className="rounded-lg overflow-hidden border border-gray-300" style={{ height: '500px' }}>
              <MapContainer 
                center={mapCenter} 
                zoom={zoom} 
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                />
                
                <Marker position={mapCenter} icon={defaultIcon}>
                  <Popup>
                    <div>
                      <h4 className="font-semibold mb-2">Selected Coordinates</h4>
                      <p><span className="font-medium">Latitude:</span> {lat}</p>
                      <p><span className="font-medium">Longitude:</span> {lon}</p>
                      {result && (
                        <>
                          <p className="mt-2"><span className="font-medium">Tile X:</span> {result.tile_x}</p>
                          <p><span className="font-medium">Tile Y:</span> {result.tile_y}</p>
                          <p><span className="font-medium">Zoom:</span> {result.zoom}</p>
                        </>
                      )}
                    </div>
                  </Popup>
                </Marker>
              </MapContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TileFinder;
