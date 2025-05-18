import React, { useState } from 'react';
import Layout from '../Layouts/Layout';
import PoiVerifier from '../Components/PoiVerifier';
import TileFinder from '../Components/TileFinder';
import StatsOverview from '../Components/StatsOverview';

function Tools() {
  const [activeTab, setActiveTab] = useState('poi-verifier');

  return (
    <Layout>
      <div className="tools-container">
        <div className="page-header mb-8">
          <h1 className="text-3xl font-bold text-gray-800 mb-2">HERE Mexico Hackathon Tools</h1>
          <p className="text-gray-600 text-center max-w-3xl mx-auto">
            A suite of tools for POI verification, map tile calculations, and dataset statistics analysis for the HERE Mexico Hackathon project.
          </p>
        </div>
        
        <div className="tool-tabs bg-white rounded-xl shadow-lg overflow-hidden">
          <div className="tab-navigation bg-gray-100 p-4 flex flex-wrap">
            <button 
              className={`tab-button transition-all duration-200 ${activeTab === 'poi-verifier' ? 'active bg-blue-600 text-white' : 'hover:bg-gray-200'}`}
              onClick={() => setActiveTab('poi-verifier')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 mr-2 inline-block">
                <path fillRule="evenodd" d="M11.54 22.351l.07.04.028.016a.76.76 0 00.723 0l.028-.015.071-.041a16.975 16.975 0 001.144-.742 19.58 19.58 0 002.683-2.282c1.944-1.99 3.963-4.98 3.963-8.827a8.25 8.25 0 00-16.5 0c0 3.846 2.02 6.837 3.963 8.827a19.58 19.58 0 002.682 2.282 16.975 16.975 0 001.145.742zM12 13.5a3 3 0 100-6 3 3 0 000 6z" clipRule="evenodd" />
              </svg>
              POI Verifier
            </button>
            <button 
              className={`tab-button transition-all duration-200 ${activeTab === 'tile-finder' ? 'active bg-blue-600 text-white' : 'hover:bg-gray-200'}`}
              onClick={() => setActiveTab('tile-finder')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 mr-2 inline-block">
                <path d="M13.5 4.06c0-1.336-1.616-2.005-2.56-1.06l-4.5 4.5H4.508c-1.141 0-2.318.664-2.66 1.905A9.76 9.76 0 001.5 12c0 .898.121 1.768.35 2.595.341 1.24 1.518 1.905 2.659 1.905h1.93l4.5 4.5c.945.945 2.561.276 2.561-1.06V4.06zM18.584 5.106a.75.75 0 011.06 0c3.808 3.807 3.808 9.98 0 13.788a.75.75 0 11-1.06-1.06 8.25 8.25 0 000-11.668.75.75 0 010-1.06z" />
                <path d="M15.932 7.757a.75.75 0 011.061 0 6 6 0 010 8.486.75.75 0 01-1.06-1.061 4.5 4.5 0 000-6.364.75.75 0 010-1.06z" />
              </svg>
              Tile Finder
            </button>
            <button 
              className={`tab-button transition-all duration-200 ${activeTab === 'stats-overview' ? 'active bg-blue-600 text-white' : 'hover:bg-gray-200'}`}
              onClick={() => setActiveTab('stats-overview')}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5 mr-2 inline-block">
                <path d="M18.375 2.25c-1.035 0-1.875.84-1.875 1.875v15.75c0 1.035.84 1.875 1.875 1.875h.75c1.035 0 1.875-.84 1.875-1.875V4.125c0-1.036-.84-1.875-1.875-1.875h-.75zM9.75 8.625c0-1.036.84-1.875 1.875-1.875h.75c1.036 0 1.875.84 1.875 1.875v11.25c0 1.035-.84 1.875-1.875 1.875h-.75a1.875 1.875 0 01-1.875-1.875V8.625zM3 13.125c0-1.036.84-1.875 1.875-1.875h.75c1.036 0 1.875.84 1.875 1.875v6.75c0 1.035-.84 1.875-1.875 1.875h-.75A1.875 1.875 0 013 19.875v-6.75z" />
              </svg>
              Dataset Statistics
            </button>
          </div>
          
          <div className="tab-content p-6">
            <div id="poi-verifier" className={`tool-section ${activeTab !== 'poi-verifier' ? 'hidden' : ''}`}>
              <PoiVerifier />
            </div>
            
            <div id="tile-finder" className={`tool-section ${activeTab !== 'tile-finder' ? 'hidden' : ''}`}>
              <TileFinder />
            </div>
            
            <div id="stats-overview" className={`tool-section ${activeTab !== 'stats-overview' ? 'hidden' : ''}`}>
              <StatsOverview />
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}

export default Tools;
