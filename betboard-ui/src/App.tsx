import React, { Component } from "react";
import logo from "./logo.svg";
import "./App.css";
import { BrowserRouter as Router, Switch, Route } from "react-router-dom";
import { Navbar, Nav } from "react-bootstrap";
import "bootstrap/dist/css/bootstrap.min.css";
import {
  XYPlot,
  XAxis,
  YAxis,
  HorizontalGridLines,
  LineSeries,
} from "react-vis";
import json_data from "./resources/data/test.json";

class App extends Component {
  render() {
    return (
      <div className="App">
        <header className="App-header">
          <Navbar expand="lg" className="Navbar">
            <Navbar.Brand className="Navbar-brand" href="/">
              BetBoard
            </Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
              <Nav className="mr-auto">
                <Nav.Link className="Navbar-link" href="/chart">
                  Charts
                </Nav.Link>
                <Nav.Link className="Navbar-link" href="/past">
                  Past Dates
                </Nav.Link>
              </Nav>
            </Navbar.Collapse>
          </Navbar>
        </header>
        <body className="App-body">
          <Router>
            <Switch>
              <Route path="/chart">
                <ChartPage />
              </Route>
              <Route path="/">
                <MainPage />
              </Route>
            </Switch>
          </Router>
        </body>
      </div>
    );
  }
}

class MainPage extends Component {
  render() {
    return (
      <div>
        <img src={logo} className="App-logo" alt="logo" />
        <p>"I have a page in simple html, I am programmer now"</p>
        <i className="Citate-owner">M. Kitli</i>
        <a
          className="App-link"
          href="https://github.com/matiktli"
          target="_blank"
          rel="noopener noreferrer"
        >
          My Git
        </a>
      </div>
    );
  }
}

class ChartPage extends Component {
  render() {
    return (
      <div>
        <XYPlot width={300} height={300}>
          <HorizontalGridLines style={{ stroke: "#B7E9ED" }} />
          <XAxis title="X Axis" />
          <YAxis title="Y Axis" />
          <LineSeries data={json_data.chart_1.data} />
        </XYPlot>
      </div>
    );
  }
}

export default App;
