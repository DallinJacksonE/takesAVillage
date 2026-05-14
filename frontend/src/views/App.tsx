import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import Home from "./Home";
import Play from "./Play";
import Instructions from "./Instructions";
import Research from "./Research";
import Gameplay from "./Gameplay";
import "./App.css";

const App: React.FC = () => {
  return (
    <Router>
      <div className='container'>
        <header className='nav-header'>
          <Link to='/' style={{ textDecoration: "none", color: "inherit" }}>
            <h2>Takes a Village</h2>
          </Link>
          <nav>
            <Link to='/play' className='nav-link'>
              Play
            </Link>
            <Link to='/instructions' className='nav-link'>
              Instructions
            </Link>
            <Link to='/research' className='nav-link'>
              Research
            </Link>
          </nav>
        </header>

        <Routes>
          <Route path='/' element={<Home />} />
          <Route path='/play' element={<Play />} />
          <Route path='/game/:gameId' element={<Gameplay />} />
          <Route path='/instructions' element={<Instructions />} />
          <Route path='/research' element={<Research />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
