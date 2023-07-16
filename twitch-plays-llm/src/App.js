import React, { useEffect, useState, useRef } from 'react';
import axios from 'axios';

// ProgressBar component displays a progress bar 
// given the current count, total, and color
const ProgressBar = ({ count, total }) => {
  const percentage = total > 0 ? (count / total) * 100 : 0;
  const red = percentage < 50 ? 255 : Math.round(510 - 5.1 * percentage);
  const green = percentage > 50 ? 255 : Math.round(5.1 * percentage);
  const color = `rgb(${red},${green},0)`;

  // Return progress bar with calculated percentage and color
  return (
    <div className="vote-bar">
      <div className="vote-bar-progress" style={{ width: `${percentage}%`, backgroundColor: color }} />
      <div className="vote-bar-text">{`${percentage.toFixed(2)}% (${count} out of ${total})`}</div>
    </div>
  );
};



// Main App component
function App() {
  // Main App component
  const [proposals, setProposals] = useState([]);
  const [storyHistory, setStoryHistory] = useState([]);
  const [timeInfo, setTimeInfo] = useState(null);
  const proposalRef = useRef(null); // Ref for scrolling
  const storyRef = useRef(null);   // Ref for scrolling
  const [image, setImage] = useState(null);

  // Use useEffect to fetch data from server on mount and every second
  useEffect(() => {
    async function fetchData() {
      const proposalsRes = await axios.get('http://localhost:9511/proposals');
  
      // Sort the proposals by vote count in descending order
      const sortedProposals = proposalsRes.data.sort((a, b) => b.vote - a.vote);
      
      setProposals(sortedProposals);
  
      const storyHistoryRes = await axios.get('http://localhost:9511/story-history');
      setStoryHistory(storyHistoryRes.data);
  
      const timeInfo = await axios.get('http://localhost:9511/vote-time-remaining')
      setTimeInfo(timeInfo.data);

      const imageRes = await axios.post('http://localhost:9511/generate-image');
      setImage(imageRes.data.image);
    }
  
    fetchData();  // Fetch data immediately on component mount
    const intervalId = setInterval(fetchData, 1000);  // Fetch data every second
  
    // Clean up function: This will be run when the component is unmounted
    return () => clearInterval(intervalId);
  }, []);

  useEffect(() => {  // New useEffect for scrolling
    proposalRef.current?.scrollIntoView({ behavior: 'smooth' });
    storyRef.current?.scrollIntoView({ behavior: 'smooth' });  // Scroll to bottom of story
  }, [proposals, storyHistory]);  // Trigger when proposals or storyHistory changes


  // Define badge style
  const badgeStyle = {
    display: "inline-block",
    padding: ".2em .6em .3em",
    fontSize: "75%",
    fontWeight: "700",
    lineHeight: "1",
    color: "#dddddd",
    textAlign: "center",
    whiteSpace: "nowrap",
    verticalAlign: "baseline",
    borderRadius: ".25em",
    backgroundColor: "#494949",
    margin: "0 5px"
  };

  // Calculate total votes
  const totalVotes = Math.max(1, proposals.map(x => x.vote).reduce((a, b) => a + b, 0));
  return (
    <div className="site-container">
      <div className="page-column main-column">
        <h2 style={{ marginBottom: '0px' }}>Story</h2>
        {storyHistory.map((entry, index) => (
          <div key={index} className="card" ref={index === storyHistory.length - 1 ? storyRef : null}>
            {entry.story_action ? <p><i>{entry.story_action}</i></p> : <></>}
            <p>{entry.narration_result}</p>
          </div>
        ))}
        {image && <img src={image} alt="Generated scene" />}
      </div>

      <div className="page-column chat-column">
        <div className="image-container">
          <img src="https://wallpapercave.com/wp/wp4471362.jpg" />
        </div>
        <h2 style={{ marginBottom: '0px' }}>Proposals</h2>
        <div className="proposals">
          {timeInfo ? <ProgressBar count={timeInfo.seconds_remaining} total={timeInfo.total_seconds} /> : proposals?.length ? 
          <p>Loading...
              <div className="loading-image-container">
                <img src="https://raw.githubusercontent.com/Fuehnix/TwitchPlaysLLMTimeTraveler/main/twitch-plays-llm/public/gears.png"/>
              </div>
          </p> : <p>No proposals.</p>}
        </div>
        {timeInfo && proposals.map((proposal, index) => (
          <div key={index} style={{ position: 'relative' }} className="card response-card" ref={index === proposals.length - 1 ? proposalRef : null}>
            <div>
              <p><b>{index + 1}: </b>{proposal.message}</p>
            </div>
            <div>
              <ProgressBar count={proposal.vote} total={totalVotes} />
            </div>

            <div style={{ alignSelf: 'flex-start', position: 'absolute', top: 0, right: 0 }}>
              <p style={{ ...badgeStyle }}>{proposal.user}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default App;
