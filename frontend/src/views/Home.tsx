import React from "react";
import { useNavigate } from "react-router-dom";

const Home: React.FC = () => {
  const navigate = useNavigate();

  const buttonStyle: React.CSSProperties = {
    display: "block",
    width: "200px",
    margin: "20px auto",
    textAlign: "center",
  };

  return (
    <div style={{ textAlign: "center", marginTop: "10%" }}>
      <h1 style={{ fontSize: "4rem", marginBottom: "3rem" }}>
        Takes a Village
      </h1>
      <p style={{ color: "var(--light_honey)", marginBottom: "3rem", fontStyle: "italic", fontWeight: "bold" }}>
        A study on social metrics and resource scarcity.
      </p>

      <button
        className='btn'
        style={buttonStyle}
        onClick={() => navigate("/play")}
      >
        Play
      </button>
      <button
        className='btn btn-secondary'
        style={buttonStyle}
        onClick={() => navigate("/instructions")}
      >
        Instructions
      </button>
      <button
        className='btn btn-secondary'
        style={buttonStyle}
        onClick={() => navigate("/research")}
      >
        Research
      </button>
    </div>
  );
};

export default Home;
