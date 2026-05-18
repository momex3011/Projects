import React, { useState } from 'react';
import { Card, Header, Icon, Loader, Popup, Segment } from 'semantic-ui-react';
import '../App.scss';
import { PokemonCard } from '../components/PokemonCard';
import { ChatForm } from '../components/ChatForm';

const PokemonChat = () => {
  const [pokemon, setPokemon] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const [activeQuery, setActiveQuery] = useState('');

  const statusText = errorMessage
    ? activeQuery ? `Could not show results for: ${activeQuery}` : 'Resolve the error and try again.'
    : isLoading
    ? `Searching for: ${activeQuery}`
    : pokemon.length > 0
      ? `Showing ${pokemon.length} result${pokemon.length === 1 ? '' : 's'} for: ${activeQuery}`
      : 'Ready for a Pokemon question.';
  const statusIcon = errorMessage
    ? 'warning sign'
    : isLoading
      ? 'sync alternate'
      : pokemon.length > 0 ? 'check circle' : 'circle outline';

  return (
    <>
      <Header as="h2" dividing>
        PokeChat Assistant
        <Header.Subheader>Ask for Pokemon recommendations and compare the returned cards.</Header.Subheader>
      </Header>
      <Segment.Group raised>
        <Segment secondary color="red">
          <Header as="h4" className="section-header-with-help">
            <Header.Content>
              Search Prompt
              <Header.Subheader>Use a suggested prompt or type your own request.</Header.Subheader>
            </Header.Content>
            <Popup
              content="Type a custom Pokemon request, press Enter or Send, or use one of the suggestion buttons."
              position="right center"
              trigger={<Icon className="inline-help-icon" name="question circle outline" />}
            />
          </Header>
        </Segment>
        <Segment>
          <ChatForm
            setActiveQuery={setActiveQuery}
            setErrorMessage={setErrorMessage}
            setIsLoading={setIsLoading}
            setSearchResults={setPokemon}
          />
        </Segment>
        <Segment className="status-strip" aria-live="polite">
          <Icon name={statusIcon} />
          {statusText}
        </Segment>
      </Segment.Group>
      {isLoading ? (
        <Segment placeholder>
          <Loader active inline="centered" content="Loading Pokemon cards..." />
        </Segment>
      ) : null}
      {!isLoading && !errorMessage && pokemon.length === 0 ? (
        <Segment placeholder color="red">
          <Header icon>
            <span aria-hidden="true" className="empty-state-pokeball" />
            Ask the Pokedex a question
            <Header.Subheader>
              Try a suggested prompt above, or type your own Pokemon request.
            </Header.Subheader>
          </Header>
        </Segment>
      ) : null}
      {!isLoading && !errorMessage && pokemon.length > 0 ? (
        <Card.Group itemsPerRow={3} stackable centered>
          {pokemon.map((pokemonID) => <PokemonCard pokemonID={pokemonID} key={pokemonID} />)}
        </Card.Group>
      ) : null}
    </>
  );
};

export { PokemonChat };
