import React, { useEffect, useState } from 'react';
import { Button, Card, Grid, Header, Icon, Input, Label, Message, Popup, Segment } from 'semantic-ui-react';
import axios from 'axios';
import '../App.scss';
import { POKE_API, POKE_CARD } from '../AppConfig';
import { PokemonCard } from '../components/PokemonCard';

const parsePokemonID = (value) => {
  const parsedValue = Number.parseInt(value, 10);

  if (Number.isNaN(parsedValue) || parsedValue < 1) {
    return null;
  }

  return parsedValue;
};

const wrapPokemonID = (value, maxPokemon) => {
  if (!maxPokemon) {
    return Math.max(1, value);
  }

  if (value < 1) {
    return maxPokemon;
  }

  if (value > maxPokemon) {
    return 1;
  }

  return value;
};

const getAdjacentPokemonID = (currentID, direction, pokemonOptions) => {
  if (pokemonOptions.length === 0) {
    return null;
  }

  const currentIndex = pokemonOptions.indexOf(currentID);

  if (currentIndex !== -1) {
    const nextIndex = (currentIndex + direction + pokemonOptions.length) % pokemonOptions.length;
    return pokemonOptions[nextIndex];
  }

  if (direction > 0) {
    return pokemonOptions.find((optionID) => optionID > currentID) || pokemonOptions[0];
  }

  for (let index = pokemonOptions.length - 1; index >= 0; index -= 1) {
    if (pokemonOptions[index] < currentID) {
      return pokemonOptions[index];
    }
  }

  return pokemonOptions[pokemonOptions.length - 1];
};

const pokemonIDFromUrl = (url = '') => {
  const match = url.match(/\/pokemon\/(\d+)\/?$/);
  return match ? Number.parseInt(match[1], 10) : null;
};

const isStandardPokemonID = (pokemonID) => pokemonID > 0 && pokemonID < 10000;

const PokemonCardBrowser = () => {
  const [pokemonID, setPokemonID] = useState(POKE_CARD);
  const [draftID, setDraftID] = useState(String(POKE_CARD));
  const [maxPokemon, setMaxPokemon] = useState(null);
  const [pokemonOptions, setPokemonOptions] = useState([]);
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    let isActive = true;

    axios
      .get(`${POKE_API}/pokemon`, {
        params: { limit: 1 },
      })
      .then((response) => {
        if (isActive) {
          setMaxPokemon(response.data.count);
        }

        return axios.get(`${POKE_API}/pokemon`, {
          params: { limit: response.data.count },
        });
      })
      .then((response) => {
        if (isActive) {
          setPokemonOptions(
            response.data.results
              .map((pokemon) => pokemonIDFromUrl(pokemon.url))
              .filter(isStandardPokemonID)
              .sort((a, b) => a - b),
          );
        }
      })
      .catch(() => {
        if (isActive) {
          setErrorMessage('Could not load the Pokemon list. Navigation still works for direct IDs.');
        }
      });

    return () => {
      isActive = false;
    };
  }, []);

  useEffect(() => {
    setDraftID(String(pokemonID));
  }, [pokemonID]);

  const submitDraftID = () => {
    const nextPokemonID = parsePokemonID(draftID);

    if (!nextPokemonID) {
      setErrorMessage('Enter a valid Pokemon number before jumping.');
      return;
    }

    if (pokemonOptions.length > 0 && !pokemonOptions.includes(nextPokemonID)) {
      setErrorMessage(`Pokemon #${nextPokemonID} is not available as a standard Pokedex Pokemon.`);
      return;
    }

    setErrorMessage('');
    setPokemonID(nextPokemonID);
  };

  const showPreviousPokemon = () => {
    setErrorMessage('');
    setPokemonID((currentPokemonID) => (
      getAdjacentPokemonID(currentPokemonID, -1, pokemonOptions)
      || wrapPokemonID(currentPokemonID - 1, maxPokemon)
    ));
  };

  const showNextPokemon = () => {
    setErrorMessage('');
    setPokemonID((currentPokemonID) => (
      getAdjacentPokemonID(currentPokemonID, 1, pokemonOptions)
      || wrapPokemonID(currentPokemonID + 1, maxPokemon)
    ));
  };

  const showRandomPokemon = () => {
    if (pokemonOptions.length === 0) {
      setErrorMessage('The Pokemon list is still loading. Try random again in a moment.');
      return;
    }

    setErrorMessage('');
    setPokemonID(pokemonOptions[Math.floor(Math.random() * pokemonOptions.length)]);
  };

  const onJumpKeyDown = (event) => {
    if (event.key === 'Enter') {
      submitDraftID();
    }
  };

  const controlsDisabled = pokemonOptions.length === 0;
  const draftHasValue = draftID.trim() !== '';
  const draftIsValid = parsePokemonID(draftID) !== null;

  return (
    <>
      <Header as="h2" dividing>
        Pokedex Browser
        <Header.Subheader>Browse standard Pokemon entries and inspect sprites, stats, and abilities.</Header.Subheader>
      </Header>
      <Grid centered>
        <Grid.Column mobile={16} tablet={10} computer={7} largeScreen={6} widescreen={5}>
          <Segment.Group raised>
            <Segment secondary color="red" textAlign="center">
              <Button.Group fluid widths={3}>
                <Popup
                  content="Move to the previous standard Pokedex entry."
                  trigger={(
                    <Button disabled={controlsDisabled} icon labelPosition="left" onClick={showPreviousPokemon} title="Show the previous standard Pokemon">
                      <Icon name="angle left" />
                      Previous
                    </Button>
                  )}
                />
                <Popup
                  content="Move to the next standard Pokedex entry."
                  trigger={(
                    <Button disabled={controlsDisabled} icon labelPosition="right" onClick={showNextPokemon} primary title="Show the next standard Pokemon">
                      Next
                      <Icon name="angle right" />
                    </Button>
                  )}
                />
                <Popup
                  content="Pick a random standard Pokemon, avoiding special form IDs."
                  trigger={(
                    <Button disabled={controlsDisabled} icon labelPosition="left" onClick={showRandomPokemon} title="Show a random standard Pokemon">
                      <Icon name="random" />
                      Random
                    </Button>
                  )}
                />
              </Button.Group>
            </Segment>
            <Segment>
              <Input
                action={{
                  color: 'green',
                  content: 'Go',
                  disabled: draftHasValue && !draftIsValid,
                  onClick: submitDraftID,
                  title: 'Jump to this Pokemon ID',
                }}
                aria-label="Pokemon ID"
                error={draftHasValue && !draftIsValid}
                fluid
                label="Pokemon #"
                onChange={(event, { value }) => {
                  setDraftID(value);
                  if (errorMessage) {
                    setErrorMessage('');
                  }
                }}
                onKeyDown={onJumpKeyDown}
                placeholder="Jump to ID"
                value={draftID}
              />
              {draftHasValue && !draftIsValid ? (
                <Label basic color="orange" pointing>
                  Enter a positive Pokemon number.
                </Label>
              ) : null}
              <Label.Group aria-live="polite" size="large" style={{ marginTop: '1em', width: '100%' }}>
                <Label color="blue">
                  Viewing #{pokemonID}
                </Label>
                <Label basic>
                  {pokemonOptions.length ? `Standard Pokemon: ${pokemonOptions.length}` : 'Loading Pokemon...'}
                </Label>
              </Label.Group>
            </Segment>
            <Segment className="status-strip" aria-live="polite">
              <Icon name={controlsDisabled ? 'sync alternate' : 'check circle'} />
              {controlsDisabled ? 'Loading standard Pokedex entries...' : 'Ready: use buttons, type an ID, or press Enter.'}
            </Segment>
            {errorMessage ? (
              <Segment>
                <Message aria-live="assertive" negative size="small">
                  <Message.Header>That Pokemon cannot be shown</Message.Header>
                  <p>{errorMessage}</p>
                </Message>
              </Segment>
            ) : null}
          </Segment.Group>
          <Card.Group centered>
            <PokemonCard pokemonID={pokemonID} />
          </Card.Group>
        </Grid.Column>
      </Grid>
    </>
  );
};

export { PokemonCardBrowser };
