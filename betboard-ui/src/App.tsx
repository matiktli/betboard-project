import React from 'react';
import logo from './logo.svg';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <img src={logo} className="App-logo" alt="logo" />
        <p>
        "I have a page in simple html, I am programmer now"
        </p>
        <i className="Citate-owner">
        M. Kitli
        </i>
        <a
          className="App-link"
          href="https://github.com/matiktli"
          target="_blank"
          rel="noopener noreferrer"
        >
          My Git
        </a>
      </header>
    </div>
  );
}

export default App;
