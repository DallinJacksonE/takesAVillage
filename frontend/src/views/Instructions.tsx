import React from 'react';

const Instructions: React.FC = () => {
  return (
    <div className="card">
      <h1 style={{ marginBottom: '1rem' }}>How to Play: Takes a Village</h1>
      <p className="intro">
        Welcome to the Village. You are spawning in an undeveloped area with raw resources[cite: 23].
        Your goal is to survive, build developments, and manage your social reputation.
      </p>

      <div style={{ marginTop: '2rem' }}>
        <h3>The Daily Cycle</h3>
        <p>Each day is split into three phases[cite: 38]:</p>

        <div style={{ paddingLeft: '20px', borderLeft: '3px solid #333', margin: '20px 0' }}>
          <h4>1. Work Phase</h4>
          <p>
            You can choose to produce resources or build a "development"[cite: 55].
            In the beginning, you can only gather one type of resource, so you must trade to survive[cite: 26].
            If you own a development, you can employ other players to work for you.
          </p>

          <h4>2. Trade Phase</h4>
          <p>
            Trade your resources with others. Warning: Players can "cheat" in trades by promising one thing
            but delivering another[cite: 78]. Honest trade builds trust; swindling builds wealth but hurts reputation.
          </p>

          <h4>3. Rumor Phase</h4>
          <p>
            You will see rumors about other players. You can choose to believe them (altering your sentiment towards that player)
            or reject them[cite: 85]. Your sentiment towards others (Honest, Chaotic, Sinister) affects how you interact.
          </p>
        </div>

        <h3>Survival Mechanics</h3>
        <ul style={{ lineHeight: '1.6' }}>
          <li><strong>Food:</strong> You must consume 1 Food every day. If your food intake drops below 50%, you starve to death[cite: 41, 43].</li>
          <li><strong>Wood:</strong> You must burn 1 Wood every day. If you fail to burn wood, your chance of sickness increases[cite: 45].</li>
          <li><strong>Sickness:</strong> If you get sick, you cannot work, but you can still trade[cite: 46, 47].</li>
        </ul>

        <h3>Winning</h3>
        <p>
          Peace looks like steady growth. War looks like slander and seizing developments[cite: 36].
          Use your resources and social standing to survive the longest and build the most prosperous village.
        </p>
      </div>
    </div>
  );
}

export default Instructions;
