import React from "react";
import { Container, Segment } from "semantic-ui-react";
import {Outlet} from "react-router-dom";
import Navbar from "../components/Navbar";

const Layout = () => {
  return (
    <div className="app-frame">
      <Navbar />
      <Container className="app-shell">
        <Outlet />
      </Container>
      <Segment inverted vertical className="app-footer">
        <Container textAlign="center">
          Pokeverse. Data provided by{' '}
          <a href="https://pokeapi.co/" target="_blank" rel="noreferrer">
            PokeAPI
          </a>.
        </Container>
      </Segment>
    </div>
  );
};

export default Layout;
