import React from 'react';
import { useNavigate } from 'react-router-dom';

function Home() {
  const navigate = useNavigate();

  const buttonStyle = {
    display: 'block',
    width: '200px',
    margin: '20px auto',
    textAlign: 'center'
  };

  return (
    <div style={{ textAlign: 'center', marginTop: '10%' }}>
      <h1 style={{ fontSize: '3rem', marginBottom: '3rem' }}>Takes a Village</h1>
      <p style={{ color: '#666', marginBottom: '2rem', fontStyle: 'italic' }}>
        A study on social metrics and resource scarcity.
      </p>

      <button className="btn" style={buttonStyle} onClick={() => navigate('/play')}>
        Play
      </button>
      <button className="btn btn-secondary" style={buttonStyle} onClick={() => navigate('/instructions')}>
        Instructions
      </button>
      <button className="btn btn-secondary" style={buttonStyle} onClick={() => navigate('/research')}>
        Research
      </button>
    </div>
  );
}

export default Home;
