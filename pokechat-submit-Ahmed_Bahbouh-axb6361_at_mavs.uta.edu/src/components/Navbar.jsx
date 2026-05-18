import React from "react";
import { Icon, Menu, Popup } from 'semantic-ui-react'
import { NavLink, useLocation } from 'react-router-dom';

const Navigation = () => {
  const location = useLocation();

  return (
    <Menu fixed="top" inverted color="red" borderless className="Navigation">
      <Popup
        content="Go to the Pokeverse home screen."
        position="bottom left"
        trigger={(
          <Menu.Item header as={NavLink} to="/" active={location.pathname === "/"}>
            <Icon name="gamepad" />
            Pokeverse
          </Menu.Item>
        )}
      />
      <Menu.Menu position="right">
        <Popup
          content="Browse Pokemon by Pokedex ID."
          position="bottom right"
          trigger={(
            <Menu.Item as={NavLink} to="/card" active={location.pathname === "/card"}>
              Pokedex
            </Menu.Item>
          )}
        />
        <Popup
          content="Ask the assistant for Pokemon recommendations."
          position="bottom right"
          trigger={(
            <Menu.Item as={NavLink} to="/chat" active={location.pathname === "/chat"}>
              PokeChat
            </Menu.Item>
          )}
        />
      </Menu.Menu>
    </Menu>
  );
};

export default Navigation;
