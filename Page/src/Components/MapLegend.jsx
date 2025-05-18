import React, { useState } from 'react';

// Custom map legend component
const MapLegend = () => {
  const [expanded, setExpanded] = useState(true);

  const toggleLegend = () => {
    setExpanded(!expanded);
  };

  // Define POI type descriptions
  const poiTypeDescriptions = {
    "5800": "Restaurant",
    "4013": "City Center",
    "7538": "Auto Service",
    "9535": "Convenience Store",
    "9567": "Food Shop",
    "9988": "Stationery Store",
    "7997": "Sports Center",
    "8211": "School/Educational",
    "9992": "Religious Place"
  };

  // Define color mappings for POI types
  const poiTypeColors = {
    "5800": "#FFD700", // gold
    "4013": "#0000FF", // blue
    "7538": "#FFA500", // orange
    "9535": "#008000", // green
    "9567": "#800080", // purple
    "9988": "#FFC0CB", // pink
    "7997": "#FF0000", // red
    "8211": "#00008B", // darkblue
    "9992": "#808080"  // gray
  };

  return (
    <div className={`map-legend ${expanded ? 'expanded' : 'collapsed'}`}>
      <div className="legend-header" onClick={toggleLegend}>
        <h4>Map Legend</h4>
        <span>{expanded ? '▼' : '▶'}</span>
      </div>
      
      {expanded && (
        <div className="legend-content">
          <div className="legend-section">
            <h5>POI Status</h5>
            <div className="legend-item">
              <div className="legend-marker success"></div>
              <span>Verified POI</span>
            </div>
            <div className="legend-item">
              <div className="legend-marker error"></div>
              <span>Failed Verification</span>
            </div>
            <div className="legend-item">
              <div className="legend-marker default"></div>
              <span>Unverified POI</span>
            </div>
          </div>
          
          <div className="legend-section">
            <h5>POI Types</h5>
            {Object.entries(poiTypeDescriptions).map(([type, desc]) => (
              <div className="legend-item" key={type}>
                <div className="legend-marker" style={{ backgroundColor: poiTypeColors[type] }}></div>
                <span>{desc} ({type})</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default MapLegend;
