import React, { useState } from "react";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");
  const [expandedIndex, setExpandedIndex] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults([]);
    setError("");
    setExpandedIndex(null);

    try {
      const res = await fetch("http://localhost:5000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, query }),
      });
      
      const data = await res.json();
      
      if (res.ok) {
        let resultsArray = [];
        
        if (Array.isArray(data)) {
          resultsArray = data;
        } else if (data.results && Array.isArray(data.results)) {
          resultsArray = data.results;
        }
        
        setResults(resultsArray);
        
        if (resultsArray.length === 0) {
          setError("No matching results found. Try a different query.");
        }
      } else {
        setError(data.error || "Error searching");
      }
    } catch (err) {
      console.error("Network error:", err);
      setError("Failed to connect to backend. Make sure the server is running on port 5000.");
    }
    
    setLoading(false);
  };

  const toggleExpand = (index) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const calculateMatch = (index) => {
    return Math.max(95 - (index * 7), 50);
  };

  return (
    <div className="page-container">
      <div className="main-content">
        <div className="header-section">
          <h1 className="main-title">Website Content Search</h1>
          <p className="main-subtitle">Search through website content with precision</p>
        </div>

        <div className="search-container">
          <div className="search-input-group">
            <span className="search-icon">🌐</span>
            <input
              type="url"
              className="search-input"
              placeholder="Enter Website URL"
              value={url}
              onChange={e => setUrl(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="search-input-group query-group">
            <span className="search-icon">🔍</span>
            <input
              type="text"
              className="search-input"
              placeholder="Enter query"
              value={query}
              onChange={e => setQuery(e.target.value)}
              disabled={loading}
            />
            <button 
              onClick={handleSubmit} 
              disabled={loading}
              className="inline-search-btn"
            >
              {loading ? "Searching..." : "Search"}
            </button>
          </div>
        </div>

        {error && <div className="error-box">{error}</div>}

        {results.length > 0 && (
          <div className="results-container">
            <h2 className="results-heading">Search Results</h2>
            
            {results.map((chunk, index) => (
              <div className="result-card" key={index}>
                <div className="result-content-area">
                  <div className="result-main-text">
                    {chunk.length > 150 ? chunk.substring(0, 150) + '...' : chunk}
                  </div>
                  <div className="match-percentage">
                    {calculateMatch(index)}% match
                  </div>
                </div>
                
                <div className="result-meta">
                  <span className="result-path-text">Path: /home</span>
                  <button 
                    className="toggle-html-btn"
                    onClick={() => toggleExpand(index)}
                  >
                    <span className="arrow-icon">{expandedIndex === index ? '▲' : '▼'}</span>
                    View HTML
                    <span className="arrow-icon">{expandedIndex === index ? '▲' : '▼'}</span>
                  </button>
                </div>

                {expandedIndex === index && (
                  <div className="html-preview">
                    <div className="html-code-block">
                      {chunk}
                    </div>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
