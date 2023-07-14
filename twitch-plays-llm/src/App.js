import React, { useEffect, useState } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [proposals, setProposals] = useState([]);
  const [storyHistory, setStoryHistory] = useState([]);

  useEffect(() => {
    async function fetchData() {
      const proposalsRes = await axios.get('http://localhost:9511/proposals');
      setProposals(proposalsRes.data);

      const storyHistoryRes = await axios.get('http://localhost:9511/story-history');
      setStoryHistory(storyHistoryRes.data);
    }

    fetchData();  // Fetch data immediately on component mount
    const intervalId = setInterval(fetchData, 1000);  // Fetch data every second

    // Clean up function: This will be run when the component is unmounted
    return () => clearInterval(intervalId);
}, []);

  return (
    <div className="site-container">
      <div className="main-column">
        {storyHistory.map((entry, index) => (
          <div key={index} className="story-entry">
            <p>Action: {entry.story_action}</p>
            <p>Result: {entry.narration_result}</p>
          </div>
        ))}
      </div>

      <div className="chat-column">
        {proposals.map((proposal, index) => (
          <div key={index} className="response-card">
            <p>Message: {proposal.message}</p>
            <p>Votes: {proposal.vote}</p>
            <p>user: {proposal.user}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
