import React, { useState } from "react";
import "./App.css";

function App() {
  const [url, setUrl] = useState("");
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState([]);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setResults([]);
    setError("");
    try {
      const res = await fetch("http://localhost:5000/search", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url, query }),
      });
      const data = await res.json();
      if (res.ok) {
        setResults(data);
      } else {
        setError(data.error || "Error searching");
      }
    } catch (err) {
      setError("Network error");
    }
    setLoading(false);
  };

  return (
    <div className="container">
      <h2>Website Content Search</h2>
      <form onSubmit={handleSubmit} className="form-block">
        <input
          type="text"
          placeholder="Enter website URL"
          value={url}
          onChange={e => setUrl(e.target.value)}
          required
        />
        <input
          type="text"
          placeholder="Enter search query"
          value={query}
          onChange={e => setQuery(e.target.value)}
          required
        />
        <button type="submit" disabled={loading}>
          {loading ? "Searching..." : "Search"}
        </button>
      </form>
      {error && <div className="error">{error}</div>}
      <div className="results-list">
        {results.length > 0 && <h4>Top 10 Matches:</h4>}
        {results.map((chunk, i) => (
          <div className="result-card" key={i}>
            {chunk}
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;