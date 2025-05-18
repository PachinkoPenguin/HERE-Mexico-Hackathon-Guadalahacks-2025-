import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { MapContainer, TileLayer, Marker, Popup, Polyline, LayersControl, LayerGroup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Icon } from 'leaflet';
import ReactJson from 'react-json-view';
import MapLegend from './MapLegend';

// Default marker icon
const defaultIcon = new Icon({
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

// Success marker icon (green)
const successIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

// Error marker icon (red)
const errorIcon = new Icon({
  iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
  iconSize: [25, 41],
  iconAnchor: [12, 41],
  popupAnchor: [1, -34],
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
  shadowSize: [41, 41]
});

// POI Status marker icons
const statusIcon = (status) => {
  if (status === true) return successIcon;
  if (status === false) return errorIcon;
  return defaultIcon;
};

// Custom marker icon with different colors based on POI type
const getPoiIcon = (poiType) => {
  // Colors for different POI types
  const poiColors = {
    "5800": "gold", // Restaurant
    "4013": "blue",  // City Center
    "7538": "orange", // Auto Service
    "9535": "green", // Convenience Store
    "9567": "purple", // Food Shop
    "9988": "pink", // Stationery Store
    "7997": "red", // Sports Center
    "8211": "darkblue", // School
    "9992": "gray", // Religious Place
  };

  const color = poiColors[poiType] || "blue";
  
  return new Icon({
    iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-${color}.png`,
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
    shadowSize: [41, 41]
  });
};

// Pre-defined example POIs for easy testing
const EXAMPLE_POIS = [
  {
    tileId: '4815075',
    name: 'MISCELÁNEA en CALLE GLORIA',
    linkId: '702722866',
    percfrref: '25.0'
  },
  {
    tileId: '4815075',
    name: 'EL HUEQUITO (Restaurante) en CALLE PLAN DE AYALA',
    linkId: '702721512',
    percfrref: '24.0'
  },
  {
    tileId: '4815075',
    name: 'TACO SALSA en AVENIDA JUAN PABLO II',
    linkId: '1346737015',
    percfrref: '50.0'
  }
];

const PoiVerifier = () => {
  const [poiFiles, setPoiFiles] = useState([]);
  const [streetFiles, setStreetFiles] = useState([]);
  const [selectedPoiFile, setSelectedPoiFile] = useState('');
  const [selectedStreetFile, setSelectedStreetFile] = useState('');
  const [poiData, setPoiData] = useState([]);
  const [filteredPoiData, setFilteredPoiData] = useState([]);
  const [streetData, setStreetData] = useState(null);
  const [selectedPoiIndex, setSelectedPoiIndex] = useState(-1);
  const [verificationResult, setVerificationResult] = useState(null);
  const [mapCenter, setMapCenter] = useState([19.3, -99.6]);
  const [mapZoom, setMapZoom] = useState(12);
  const [markers, setMarkers] = useState([]);
  const [streetLines, setStreetLines] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [matchedPois, setMatchedPois] = useState([]);

  // State to store popular POI types
  const [popularPoiTypes, setPopularPoiTypes] = useState([]);
  const [batchResults, setBatchResults] = useState(null);
  const [batchInProgress, setBatchInProgress] = useState(false);
  const mapRef = useRef(null);

  // New states for advanced search filters
  const [advancedSearch, setAdvancedSearch] = useState(false);
  const [filters, setFilters] = useState({
    name: '',
    linkId: '',
    poiId: '',
    side: ''
  });

  useEffect(() => {
    // Load POI and street files when component mounts
    fetchPoiFiles();
    fetchStreetFiles();
    fetchPopularPoiTypes();
  }, []);

  // Filter POIs based on search query and advanced filters
  useEffect(() => {
    if (!poiData.length) {
      setFilteredPoiData([]);
      return;
    }
    
    // If simple search is active
    if (!advancedSearch && searchQuery) {
      const lowercaseQuery = searchQuery.toLowerCase();
      const filtered = poiData.filter(poi => {
        const name = (poi.fields.POI_NAME || '').toLowerCase();
        const id = poi.fields.POI_ID.toLowerCase();
        const linkId = poi.fields.LINK_ID.toLowerCase();
        return (
          name.includes(lowercaseQuery) || 
          id.includes(lowercaseQuery) || 
          linkId.includes(lowercaseQuery)
        );
      });
      
      setFilteredPoiData(filtered);
      return;
    }
    
    // If advanced search is active
    if (advancedSearch && (filters.name || filters.linkId || filters.poiId || filters.side)) {
      const filtered = poiData.filter(poi => {
        const nameMatch = !filters.name || (poi.fields.POI_NAME || '').toLowerCase().includes(filters.name.toLowerCase());
        const linkIdMatch = !filters.linkId || poi.fields.LINK_ID.toLowerCase().includes(filters.linkId.toLowerCase());
        const poiIdMatch = !filters.poiId || poi.fields.POI_ID.toLowerCase().includes(filters.poiId.toLowerCase());
        const sideMatch = !filters.side || poi.fields.POI_ST_SD === filters.side;
        
        return nameMatch && linkIdMatch && poiIdMatch && sideMatch;
      });
      
      setFilteredPoiData(filtered);
      return;
    }
    
    // If no filters are active, show all POIs
    setFilteredPoiData(poiData);
  }, [poiData, searchQuery, advancedSearch, filters]);

  // Find POIs that match with available streets
  useEffect(() => {
    if (!poiData.length || !streetData) return;
    
    const linkIds = new Set();
    streetData.features.forEach(feature => {
      if (feature.properties && feature.properties.link_id) {
        linkIds.add(feature.properties.link_id.toString());
      }
    });
    
    const matched = poiData.filter(poi => 
      poi.fields.LINK_ID && linkIds.has(poi.fields.LINK_ID)
    ).slice(0, 25); // Limit to 25 matches
    
    setMatchedPois(matched);
  }, [poiData, streetData]);

  const fetchPoiFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/list-poi-files');
      setPoiFiles(response.data.files);
    } catch (err) {
      setError('Error fetching POI files: ' + err.message);
    }
  };

  const fetchStreetFiles = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/list-street-files');
      setStreetFiles(response.data.files);
    } catch (err) {
      setError('Error fetching street files: ' + err.message);
    }
  };

  const fetchPopularPoiTypes = async () => {
    try {
      const response = await axios.get('http://localhost:5001/api/popular-pois');
      setPopularPoiTypes(response.data.popular_poi_types || []);
    } catch (err) {
      console.error('Error fetching popular POI types:', err);
    }
  };

  const handlePoiFileSelect = async (e) => {
    const filename = e.target.value;
    setSelectedPoiFile(filename);
    if (filename) {
      try {
        setLoading(true);
        const response = await axios.get(`http://localhost:5001/api/read-poi-file?filename=${filename}`);
        // Parse CSV lines into array of objects
        const lines = response.data.lines;
        const parsedData = lines.map(line => {
          const fields = line.trim().split(',');
          return {
            csv_line: line,
            fields: {
              POI_ID: fields[0] || '',
              LINK_ID: fields[1] || '',
              POI_TYPE: fields[4] || '',
              POI_NAME: fields[5] || '',
              POI_ST_SD: fields[13] || 'R',
              PERCFRREF: fields[22] || (fields[20] || '')
            }
          };
        });
        setPoiData(parsedData);
        setSearchQuery(''); // Reset search query
        setLoading(false);
        
        // Auto-select matching street file if not already selected
        if (!selectedStreetFile) {
          const tileId = filename.replace('POI_', '').replace('.csv', '');
          const matchingStreetFile = `SREETS_NAV_${tileId}.geojson`;
          if (streetFiles.includes(matchingStreetFile)) {
            setSelectedStreetFile(matchingStreetFile);
            loadStreetFile(matchingStreetFile);
          }
        }
      } catch (err) {
        setError('Error reading POI file: ' + err.message);
        setLoading(false);
      }
    }
  };

  const loadStreetFile = async (filename) => {
    if (filename) {
      try {
        setLoading(true);
        const response = await axios.get(`http://localhost:5001/api/read-street-file?filename=${filename}`);
        setStreetData(response.data.data);
        
        // Process street data to display on map
        processStreetData(response.data.data);
        setLoading(false);
      } catch (err) {
        setError('Error reading street file: ' + err.message);
        setLoading(false);
      }
    }
  };

  const handleStreetFileSelect = async (e) => {
    const filename = e.target.value;
    setSelectedStreetFile(filename);
    await loadStreetFile(filename);
    
    // Auto-select matching POI file if not already selected
    if (!selectedPoiFile && filename) {
      const tileId = filename.replace('SREETS_NAV_', '').replace('.geojson', '');
      const matchingPoiFile = `POI_${tileId}.csv`;
      if (poiFiles.includes(matchingPoiFile)) {
        setSelectedPoiFile(matchingPoiFile);
        handlePoiFileSelect({ target: { value: matchingPoiFile } });
      }
    }
  };

  const processStreetData = (data) => {
    if (!data || !data.features) return;
    
    // Extract street lines for display
    const lines = [];
    const allCoords = [];
    
    data.features.forEach(feature => {
      if (feature.geometry && feature.geometry.coordinates) {
        const coords = feature.geometry.coordinates;
        
        // Handle different geometry types
        if (feature.geometry.type === 'LineString') {
          // Convert from [lon, lat] to [lat, lon] for Leaflet
          const lineCoords = coords.map(coord => [coord[1], coord[0]]);
          lines.push(lineCoords);
          allCoords.push(...lineCoords);
        } else if (feature.geometry.type === 'MultiLineString') {
          coords.forEach(line => {
            const lineCoords = line.map(coord => [coord[1], coord[0]]);
            lines.push(lineCoords);
            allCoords.push(...lineCoords);
          });
        }
      }
    });
    
    setStreetLines(lines);
    
    // Set map center to the average of all coordinates
    if (allCoords.length > 0) {
      const avg = allCoords.reduce(
        (acc, coord) => [acc[0] + coord[0]/allCoords.length, acc[1] + coord[1]/allCoords.length], 
        [0, 0]
      );
      setMapCenter(avg);
    }
  };

  const handlePoiSelect = (index) => {
    setSelectedPoiIndex(index);
  };

  const loadExample = async (example) => {
    // Load the POI and street files for the example
    const poiFile = `POI_${example.tileId}.csv`;
    const streetFile = `SREETS_NAV_${example.tileId}.geojson`;
    
    if (!poiFiles.includes(poiFile) || !streetFiles.includes(streetFile)) {
      setError(`Example files not available: ${poiFile}, ${streetFile}`);
      return;
    }
    
    setSelectedPoiFile(poiFile);
    setSelectedStreetFile(streetFile);
    
    try {
      setLoading(true);
      
      // Load street file
      const streetResponse = await axios.get(`http://localhost:5001/api/read-street-file?filename=${streetFile}`);
      setStreetData(streetResponse.data.data);
      processStreetData(streetResponse.data.data);
      
      // Load POI file
      const poiResponse = await axios.get(`http://localhost:5001/api/read-poi-file?filename=${poiFile}`);
      const lines = poiResponse.data.lines;
      const parsedData = lines.map(line => {
        const fields = line.trim().split(',');
        return {
          csv_line: line,
          fields: {
            POI_ID: fields[0] || '',
            LINK_ID: fields[1] || '',
            POI_NAME: fields[5] || '',
            POI_ST_SD: fields[13] || 'R',
            PERCFRREF: fields[22] || (fields[20] || '')
          }
        };
      });
      setPoiData(parsedData);
      
      // Find and select the example POI
      setSearchQuery(example.linkId);
      const poiIndex = parsedData.findIndex(poi => 
        poi.fields.LINK_ID === example.linkId && 
        poi.fields.PERCFRREF === example.percfrref
      );
      
      if (poiIndex >= 0) {
        setSelectedPoiIndex(poiIndex);
        // Auto-verify the POI
        setTimeout(() => {
          verifyPoiWithIndex(poiIndex, parsedData, streetResponse.data.data);
        }, 500);
      }
      
      setLoading(false);
    } catch (err) {
      setError('Error loading example: ' + err.message);
      setLoading(false);
    }
  };

  const verifyPoiWithIndex = async (index, pois, streets) => {
    if (index < 0 || !streets) {
      setError('Please select a POI and a street file first');
      return;
    }
    
    try {
      setLoading(true);
      const selectedPoi = pois[index];
      
      // Find the corresponding street segment by LINK_ID
      let matchingStreet = null;
      if (streets && streets.features) {
        matchingStreet = streets.features.find(
          feature => feature.properties.link_id && 
            feature.properties.link_id.toString() === selectedPoi.fields.LINK_ID.toString()
        );
      }
      
      if (!matchingStreet) {
        // If no matching street found, try using the auto-match feature in the API
        const response = await axios.post('http://localhost:5001/api/verify-poi', {
          type: 'csv',
          data: {
            csv_line: selectedPoi.csv_line,
            link_id: selectedPoi.fields.LINK_ID,
            street_file: selectedStreetFile
          }
        });
        
        setVerificationResult(response.data);          // Update markers on the map if coordinates are returned
          if (response.data.coordenadas) {
            const [lon, lat] = response.data.coordenadas;
            setMarkers([{
              position: [lat, lon],
              title: selectedPoi.fields.POI_NAME,
              description: `POI ID: ${selectedPoi.fields.POI_ID}, Link ID: ${selectedPoi.fields.LINK_ID}`,
              poiType: selectedPoi.fields.POI_TYPE || ''
            }]);
            
            // Center map on the POI
            setMapCenter([lat, lon]);
            setMapZoom(16);
          }
      } else {
        // Extract coordinates from the matching street
        const nodos = matchingStreet.geometry.coordinates;
        
        // Call the API to verify the POI
        const response = await axios.post('http://localhost:5001/api/verify-poi', {
          type: 'csv',
          data: {
            csv_line: selectedPoi.csv_line,
            nodos: nodos
          }
        });
        
        setVerificationResult(response.data);          // Update markers on the map
          if (response.data.coordenadas) {
            const [lon, lat] = response.data.coordenadas;
            setMarkers([{
              position: [lat, lon],
              title: selectedPoi.fields.POI_NAME,
              description: `POI ID: ${selectedPoi.fields.POI_ID}, Link ID: ${selectedPoi.fields.LINK_ID}`,
              poiType: selectedPoi.fields.POI_TYPE || '',
              status: true
            }]);
            
            // Center map on the POI
            setMapCenter([lat, lon]);
            setMapZoom(16);y
          }
      }
      
      setLoading(false);
    } catch (err) {
      setError('Error verifying POI: ' + err.message);
      setLoading(false);
    }
  };

  const verifyPoi = () => {
    verifyPoiWithIndex(selectedPoiIndex, poiData, streetData);
  };

  // Function to find matching POIs for selected files
  const findMatches = async () => {
    if (!selectedPoiFile || !selectedStreetFile) {
      setError('Please select both POI and street files first');
      return;
    }

    try {
      setLoading(true);
      const response = await axios.get(
        `http://localhost:5001/api/find-matches?poi_file=${selectedPoiFile}&street_file=${selectedStreetFile}`
      );
      
      if (response.data.matches && response.data.matches.length > 0) {
        // Update the list of matched POIs
        const matches = response.data.matches.map(match => ({
          csv_line: match.csv_line,
          fields: {
            POI_ID: match.poi_id,
            LINK_ID: match.link_id,
            POI_NAME: match.name,
            POI_ST_SD: match.side,
            PERCFRREF: match.perc
          }
        }));
        
        setMatchedPois(matches);
        setSearchQuery(''); // Clear search filter
        
        // Show success message
        setError(''); // Clear any previous errors
      } else {
        setError(`No matches found between ${selectedPoiFile} and ${selectedStreetFile}`);
      }
      
      setLoading(false);
    } catch (err) {
      setError('Error finding matches: ' + err.message);
      setLoading(false);
    }
  };

  // Function to verify multiple POIs at once
  const batchVerifyPois = async () => {
    if (!selectedStreetFile || matchedPois.length === 0) {
      setError('Please select a street file and ensure there are matched POIs');
      return;
    }

    try {
      setBatchInProgress(true);
      setError('');
      
      // Prepare the batch of POIs to verify
      const poiItems = matchedPois.map(poi => ({
        poi_id: poi.fields.POI_ID,
        link_id: poi.fields.LINK_ID,
        csv_line: poi.csv_line
      }));
      
      const response = await axios.post('http://localhost:5001/api/batch-verify-pois', {
        poi_items: poiItems,
        street_file: selectedStreetFile
      });
      
      setBatchResults(response.data);
      
      // Update display to show batch results
      if (response.data.batch_results && response.data.batch_results.length > 0) {
        // Extract coordinates from the results to show on map
        const resultMarkers = response.data.batch_results
          .filter(result => result.success && result.coordenadas)
          .map(result => {
            const [lon, lat] = result.coordenadas;
            return {
              position: [lat, lon],
              title: matchedPois.find(p => p.fields.POI_ID === result.poi_id)?.fields.POI_NAME || 'POI',
              description: `POI ID: ${result.poi_id}, Status: ${result.success ? 'Verified' : 'Failed'}`,
              poiType: matchedPois.find(p => p.fields.POI_ID === result.poi_id)?.fields.POI_TYPE || '',
              status: result.success
            };
          });
        
        if (resultMarkers.length > 0) {
          setMarkers(resultMarkers);
          
          // Calculate center point of all markers
          const sumLat = resultMarkers.reduce((sum, marker) => sum + marker.position[0], 0);
          const sumLon = resultMarkers.reduce((sum, marker) => sum + marker.position[1], 0);
          const avgLat = sumLat / resultMarkers.length;
          const avgLon = sumLon / resultMarkers.length;
          
          setMapCenter([avgLat, avgLon]);
          setMapZoom(15); // Zoom out a bit to see multiple markers
        }
      }
      
      setBatchInProgress(false);
    } catch (err) {
      setError('Error during batch verification: ' + err.message);
      setBatchInProgress(false);
    }
  };

  // Handle filter changes
  const handleFilterChange = (field, value) => {
    setFilters({
      ...filters,
      [field]: value
    });
  };

  // Reset filters
  const resetFilters = () => {
    setFilters({
      name: '',
      linkId: '',
      poiId: '',
      side: ''
    });
    setSearchQuery('');
  };

  return (
    <div className="poi-verifier-container">
      <h2>POI Verification Tool</h2>
      
      {error && <div className="error-message">{error}</div>}
      
      <div className="quick-examples">
        <h3>Quick Examples</h3>
        <div className="example-buttons">
          {EXAMPLE_POIS.map((example, index) => (
            <button 
              key={index} 
              onClick={() => loadExample(example)}
              disabled={loading}
              className="example-button"
            >
              {example.name}
            </button>
          ))}
        </div>
      </div>
      
      {popularPoiTypes.length > 0 && (
        <div className="popular-poi-types">
          <h3>Popular POI Categories</h3>
          <div className="poi-category-list">
            {popularPoiTypes.map((category, idx) => (
              <div key={idx} className="poi-category">
                <h4>{category.type_name}</h4>
                <ul>
                  {category.examples.map((example, exIdx) => (
                    <li key={exIdx}>
                      <button 
                        className="poi-example-button"
                        onClick={() => {
                          // Load the appropriate files and select this POI
                          const poiFile = example.file;
                          const streetFile = poiFile.replace('POI_', 'SREETS_NAV_').replace('.csv', '.geojson');
                          
                          setSelectedPoiFile(poiFile);
                          setSelectedStreetFile(streetFile);
                          handlePoiFileSelect({ target: { value: poiFile }});
                          handleStreetFileSelect({ target: { value: streetFile }});
                          
                          // Set search query to help find this POI
                          setSearchQuery(example.name);
                        }}
                      >
                        {example.name}
                      </button>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}
      
      <div className="file-selection">
        <div className="input-group">
          <label>POI File:</label>
          <select onChange={handlePoiFileSelect} value={selectedPoiFile}>
            <option value="">Select a POI file</option>
            {poiFiles.map((file, index) => (
              <option key={index} value={file}>{file}</option>
            ))}
          </select>
        </div>
        
        <div className="input-group">
          <label>Street File:</label>
          <select onChange={handleStreetFileSelect} value={selectedStreetFile}>
            <option value="">Select a street file</option>
            {streetFiles.map((file, index) => (
              <option key={index} value={file}>{file}</option>
            ))}
          </select>
        </div>
        
        <div className="input-group file-actions">
          <button 
            className="find-matches-button"
            onClick={findMatches}
            disabled={!selectedPoiFile || !selectedStreetFile || loading}
          >
            {loading ? 'Finding...' : 'Find Matching POIs'}
          </button>
        </div>
      </div>
      
      <div className="content-area">
        <div className="poi-list-container">
          <div className="poi-search">
            {!advancedSearch ? (
              <>
                <input
                  type="text"
                  placeholder="Search POIs by name, ID, or Link ID..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="search-input"
                />
                <button 
                  className="advanced-search-toggle"
                  onClick={() => setAdvancedSearch(true)}
                >
                  Advanced Search
                </button>
              </>
            ) : (
              <div className="advanced-search-container">
                <div className="advanced-search-header">
                  <h4>Advanced Search</h4>
                  <button 
                    className="advanced-search-toggle"
                    onClick={() => setAdvancedSearch(false)}
                  >
                    Simple Search
                  </button>
                </div>
                <div className="advanced-search-fields">
                  <div className="advanced-search-field">
                    <label>POI Name:</label>
                    <input
                      type="text"
                      placeholder="Filter by name..."
                      value={filters.name}
                      onChange={(e) => handleFilterChange('name', e.target.value)}
                    />
                  </div>
                  <div className="advanced-search-field">
                    <label>Link ID:</label>
                    <input
                      type="text"
                      placeholder="Filter by Link ID..."
                      value={filters.linkId}
                      onChange={(e) => handleFilterChange('linkId', e.target.value)}
                    />
                  </div>
                  <div className="advanced-search-field">
                    <label>POI ID:</label>
                    <input
                      type="text"
                      placeholder="Filter by POI ID..."
                      value={filters.poiId}
                      onChange={(e) => handleFilterChange('poiId', e.target.value)}
                    />
                  </div>
                  <div className="advanced-search-field">
                    <label>Side:</label>
                    <select
                      value={filters.side}
                      onChange={(e) => handleFilterChange('side', e.target.value)}
                    >
                      <option value="">Any</option>
                      <option value="R">Right (R)</option>
                      <option value="L">Left (L)</option>
                    </select>
                  </div>
                </div>
                <div className="advanced-search-actions">
                  <button 
                    className="reset-filters-button"
                    onClick={resetFilters}
                  >
                    Reset Filters
                  </button>
                </div>
              </div>
            )}
          </div>
          
          {matchedPois.length > 0 && (
            <div className="matched-pois">
              <h4>POIs with Matching Streets ({matchedPois.length})</h4>
              <ul>
                {matchedPois.map((poi, index) => (
                  <li 
                    key={`match-${index}`} 
                    onClick={() => {
                      const fullIndex = poiData.findIndex(p => p.fields.POI_ID === poi.fields.POI_ID);
                      if (fullIndex >= 0) handlePoiSelect(fullIndex);
                    }}
                    className={poiData.findIndex(p => p.fields.POI_ID === poi.fields.POI_ID) === selectedPoiIndex ? 'selected' : ''}
                  >
                    <strong>{poi.fields.POI_NAME || `POI ${index + 1}`}</strong>
                    <br/>
                    <small>Link ID: {poi.fields.LINK_ID}</small>
                  </li>
                ))}
              </ul>
            </div>
          )}
          
          <div className="poi-list">
            <h4>All POIs ({filteredPoiData.length})</h4>
            {loading ? (
              <div>Loading...</div>
            ) : (
              <ul>
                {filteredPoiData.map((poi, index) => {
                  const originalIndex = poiData.findIndex(p => p.fields.POI_ID === poi.fields.POI_ID);
                  return (
                    <li 
                      key={index} 
                      className={selectedPoiIndex === originalIndex ? 'selected' : ''}
                      onClick={() => handlePoiSelect(originalIndex)}
                    >
                      <strong>{poi.fields.POI_NAME || `POI ${index + 1}`}</strong>
                      <br/>
                      <small>ID: {poi.fields.POI_ID}, Link ID: {poi.fields.LINK_ID}</small>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
        
        <div className="map-container">
          <MapContainer 
            center={mapCenter} 
            zoom={mapZoom} 
            style={{ height: '500px', width: '100%' }}
            ref={mapRef}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            <LayersControl position="topright">
              <LayerGroup name="Street Lines">
                {streetLines.map((line, index) => (
                  <Polyline 
                    key={index} 
                    positions={line} 
                    color="blue" 
                    weight={3}
                  />
                ))}
              </LayerGroup>
              
              <LayerGroup name="POI Markers">
                {markers.map((marker, index) => {
                  const markerIcon = marker.status !== undefined ? 
                    (marker.status ? successIcon : errorIcon) : 
                    (marker.poiType ? getPoiIcon(marker.poiType) : defaultIcon);
                    
                  return (
                    <Marker 
                      key={index} 
                      position={marker.position} 
                      icon={markerIcon}
                    >
                      <Popup>
                        <div className="marker-popup">
                          <h4>{marker.title}</h4>
                          <p>{marker.description}</p>
                          {marker.poiType && (
                            <p><strong>Type:</strong> {marker.poiType}</p>
                          )}
                          {marker.status !== undefined && (
                            <p><strong>Status:</strong> 
                              <span className={marker.status ? "success-text" : "error-text"}>
                                {marker.status ? "Verified" : "Failed"}
                              </span>
                            </p>
                          )}
                        </div>
                      </Popup>
                    </Marker>
                  );
                })}
              </LayerGroup>
            </LayersControl>
          </MapContainer>
        </div>
      </div>
      
      <div className="action-area">
        <button 
          className="verify-button" 
          onClick={verifyPoi} 
          disabled={selectedPoiIndex < 0 || !streetData || loading}
        >
          {loading ? 'Processing...' : 'Verify POI'}
        </button>
        
        <button 
          className="find-matches-button" 
          onClick={findMatches} 
          disabled={loading}
        >
          {loading ? 'Finding...' : 'Find Matching POIs'}
        </button>
        
        <button 
          className="batch-verify-button" 
          onClick={batchVerifyPois} 
          disabled={!selectedStreetFile || matchedPois.length === 0 || batchInProgress}
        >
          {batchInProgress ? 'Verifying Batch...' : `Verify All Matched POIs (${matchedPois.length})`}
        </button>
      </div>
      
      {verificationResult && !batchResults && (
        <div className="result-area">
          <h3>Verification Result</h3>
          <ReactJson src={verificationResult} collapsed={1} />
        </div>
      )}
      
      {batchResults && (
        <div className="batch-results-area">
          <h3>Batch Verification Results</h3>
          <div className="batch-summary">
            <div className="summary-item">
              <span className="label">Total Processed:</span>
              <span className="value">{batchResults.total_processed}</span>
            </div>
            <div className="summary-item">
              <span className="label">Successfully Verified:</span>
              <span className="value success">{batchResults.success_count}</span>
            </div>
            <div className="summary-item">
              <span className="label">Failed:</span>
              <span className="value error">{batchResults.total_processed - batchResults.success_count}</span>
            </div>
          </div>
          
          <div className="batch-results-list">
            <h4>Individual Results</h4>
            <div className="results-table-container">
              <table className="results-table">
                <thead>
                  <tr>
                    <th>POI ID</th>
                    <th>Name</th>
                    <th>Status</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {batchResults.batch_results.map((result, idx) => {
                    const poi = matchedPois.find(p => p.fields.POI_ID === result.poi_id);
                    return (
                      <tr key={idx} className={result.success ? 'success-row' : 'error-row'}>
                        <td>{result.poi_id}</td>
                        <td>{poi?.fields.POI_NAME || 'Unknown'}</td>
                        <td>{result.success ? 'Verified' : 'Failed'}</td>
                        <td>
                          <button 
                            className="details-button"
                            onClick={() => {
                              // Find the POI in the original data to select it
                              const fullIndex = poiData.findIndex(p => p.fields.POI_ID === result.poi_id);
                              if (fullIndex >= 0) {
                                handlePoiSelect(fullIndex);
                                setVerificationResult(result);
                                setBatchResults(null);
                              }
                            }}
                          >
                            View Details
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
          
          <div className="batch-actions">
            <button 
              className="export-button"
              onClick={() => {
                // Export results as CSV
                const csvContent = [
                  'POI_ID,Name,Status,Latitude,Longitude',
                  ...batchResults.batch_results.map(result => {
                    const poi = matchedPois.find(p => p.fields.POI_ID === result.poi_id);
                    const coords = result.coordenadas || [0, 0];
                    return `${result.poi_id},"${poi?.fields.POI_NAME || 'Unknown'}",${result.success ? 'Verified' : 'Failed'},${coords[1]},${coords[0]}`;
                  })
                ].join('\n');
                
                const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
                const url = URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.setAttribute('href', url);
                link.setAttribute('download', `poi_verification_results_${new Date().toISOString().slice(0,10)}.csv`);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
              }}
            >
              Export Results as CSV
            </button>
            <button 
              className="reset-button"
              onClick={() => {
                setBatchResults(null);
                setMarkers([]);
              }}
            >
              Clear Results
            </button>
          </div>
        </div>
      )}
      
      {loading && (
        <div className="loading-overlay">
          <div className="loading-spinner"></div>
          <div className="loading-message">Processing... Please wait</div>
        </div>
      )}
      
      <MapLegend />
    </div>
  );
};

export default PoiVerifier;
