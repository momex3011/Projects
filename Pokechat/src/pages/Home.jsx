import React from 'react';
import { Button, Divider, Header, Icon, Popup, Segment } from 'semantic-ui-react';
import { Link } from 'react-router-dom';

const Home = () => {
  return (
    <Segment textAlign="center" padded="very" piled color="red" className="home-panel">
      <Header as="h1" textAlign="center">
        <Icon name="gamepad" circular inverted className="home-pokedex-icon" />
        <Header.Content>
          Pokeverse
          <Header.Subheader>
            Explore the encyclopedic Pokedex or ask the AI assistant for custom recommendations.
          </Header.Subheader>
        </Header.Content>
      </Header>
      <Divider hidden />
      <Button.Group size="large">
        <Popup
          content="Browse one Pokemon at a time with exact stats, types, abilities, and sprites."
          position="bottom center"
          trigger={(
            <Button primary as={Link} to="/card" icon labelPosition="left">
              <Icon name="id card" />
              Pokedex
            </Button>
          )}
        />
        <Button.Or />
        <Popup
          content="Ask the AI for Pokemon recommendations and get card results back."
          position="bottom center"
          trigger={(
            <Button color="teal" as={Link} to="/chat" icon labelPosition="left">
              <Icon name="chat" />
              PokeChat
            </Button>
          )}
        />
      </Button.Group>
    </Segment>
  );
};
  
export default Home;
