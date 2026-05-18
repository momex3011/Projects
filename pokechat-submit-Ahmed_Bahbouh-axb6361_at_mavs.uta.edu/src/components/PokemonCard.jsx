import React, { useEffect, useState } from 'react';
import { Button, Card, Icon, Image, Label, List, Loader, Message, Popup } from 'semantic-ui-react';
import '../App.scss';
import { POKE_API } from '../AppConfig';
import axios from 'axios';

const TYPE_COLORS = {
  bug: 'olive',
  dark: 'black',
  dragon: 'violet',
  electric: 'yellow',
  fairy: 'pink',
  fighting: 'orange',
  fire: 'red',
  flying: 'blue',
  ghost: 'black',
  grass: 'green',
  ground: 'brown',
  ice: 'teal',
  normal: 'grey',
  poison: 'purple',
  psychic: 'pink',
  rock: 'brown',
  steel: 'grey',
  water: 'blue',
};

const formatName = (value = '') =>
  value
    .split('-')
    .filter(Boolean)
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(' ');

const formatStatName = (value = '') => {
  if (value === 'hp') {
    return 'HP';
  }

  return formatName(value);
};

const collectSpriteUrls = (value, urls = []) => {
  if (!value) {
    return urls;
  }

  if (typeof value === 'string' && value.startsWith('http') && !urls.includes(value)) {
    urls.push(value);
    return urls;
  }

  if (typeof value !== 'object') {
    return urls;
  }

  Object.values(value).forEach((nestedValue) => collectSpriteUrls(nestedValue, urls));
  return urls;
};

const pushSpriteUrl = (urls, value) => {
  if (typeof value === 'string' && value.startsWith('http') && !urls.includes(value)) {
    urls.push(value);
  }
};

const getSpriteUrls = (sprites = {}) => {
  const urls = [];

  [
    sprites.other?.['official-artwork']?.front_default,
    sprites.other?.['official-artwork']?.front_shiny,
    sprites.other?.home?.front_default,
    sprites.other?.home?.front_shiny,
    sprites.front_default,
    sprites.front_female,
    sprites.front_shiny,
    sprites.front_shiny_female,
    sprites.other?.showdown?.front_default,
    sprites.other?.showdown?.front_shiny,
    sprites.other?.dream_world?.front_default,
    sprites.back_default,
    sprites.back_female,
    sprites.back_shiny,
    sprites.back_shiny_female,
  ].forEach((spriteUrl) => pushSpriteUrl(urls, spriteUrl));

  return collectSpriteUrls(sprites, urls);
};

const PokemonCard = ({ pokemonID }) => {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [spriteIndex, setSpriteIndex] = useState(0);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    let isActive = true;

    setData(null);
    setError('');
    setSpriteIndex(0);

    axios
      .get(`${POKE_API}/pokemon/${pokemonID}`)
      .then((response) => {
        if (isActive) {
          setData(response.data);
        }
      })
      .catch((err) => {
        if (isActive) {
          setError(err.response?.data?.error || err.message || 'Unable to load Pokemon data.');
        }
      });

    return () => {
      isActive = false;
    };
  }, [pokemonID, retryCount]);

  if (error) {
    return (
      <Card className="pokemon-card" color="red">
        <Card.Content>
          <Card.Header>Pokemon #{pokemonID}</Card.Header>
          <Message aria-live="assertive" negative size="small">
            <Message.Header>Card failed to load</Message.Header>
            <p>{error}</p>
          </Message>
          <Button basic color="red" fluid icon labelPosition="left" onClick={() => setRetryCount((count) => count + 1)}>
            <Icon name="redo" />
            Retry card
          </Button>
        </Card.Content>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card className="pokemon-card">
        <Card.Content aria-live="polite" textAlign="center">
          <Loader active inline="centered" />
          <Card.Header style={{ marginTop: '0.75em' }}>Loading Pokemon #{pokemonID}</Card.Header>
        </Card.Content>
      </Card>
    );
  }

  const sprites = getSpriteUrls(data.sprites);
  const activeSprite = sprites[spriteIndex] || '';
  const typeNames = data.types.map(({ type }) => type.name);
  const primaryColor = TYPE_COLORS[typeNames[0]] || 'grey';
  const heightMeters = (data.height / 10).toFixed(1);
  const weightKg = (data.weight / 10).toFixed(1);
  const abilities = data.abilities.map(({ ability }) => formatName(ability.name)).join(', ');

  const showPreviousSprite = () => {
    setSpriteIndex((currentIndex) => (currentIndex === 0 ? sprites.length - 1 : currentIndex - 1));
  };

  const showNextSprite = () => {
    setSpriteIndex((currentIndex) => (currentIndex === sprites.length - 1 ? 0 : currentIndex + 1));
  };

  return (
    <Card className="pokemon-card" color={primaryColor}>
      <div className="pokemon-card__image-shell">
        <Image className="pokemon-card__image" src={activeSprite} alt={formatName(data.name)} ui={false} />
      </div>
      <Card.Content>
        <Card.Header>{formatName(data.name)}</Card.Header>
        <Card.Meta>
          #{data.id} | Base experience: {data.base_experience}
        </Card.Meta>
        <Label.Group size="tiny" style={{ marginTop: '0.75em' }}>
          {typeNames.map((typeName) => (
            <Label color={TYPE_COLORS[typeName] || 'grey'} key={typeName}>
              {formatName(typeName)}
            </Label>
          ))}
        </Label.Group>
        <List relaxed="very" divided>
          <List.Item>
            <List.Content floated="right">{heightMeters} m</List.Content>
            <List.Content>Height</List.Content>
          </List.Item>
          <List.Item>
            <List.Content floated="right">{weightKg} kg</List.Content>
            <List.Content>Weight</List.Content>
          </List.Item>
          <List.Item>
            <List.Content floated="right">{abilities}</List.Content>
            <List.Content>Abilities</List.Content>
          </List.Item>
        </List>
      </Card.Content>
      <Card.Content extra>
        <Card.Header as="h4">Base Stats</Card.Header>
        <List divided relaxed="very">
          {data.stats.map((stat) => (
            <List.Item key={stat.stat.name}>
              <List.Content floated="right">{stat.base_stat}</List.Content>
              <List.Content>{formatStatName(stat.stat.name)}</List.Content>
            </List.Item>
          ))}
        </List>
      </Card.Content>
      {sprites.length > 1 ? (
        <Card.Content extra>
          <Button.Group fluid size="mini">
            <Popup
              content="Show the previous available sprite."
              position="bottom center"
              trigger={(
                <Button aria-label="Previous sprite" icon onClick={showPreviousSprite} title="Previous sprite">
                  <Icon name="angle left" />
                </Button>
              )}
            />
            <Button disabled>
              Sprite {spriteIndex + 1}/{sprites.length}
            </Button>
            <Popup
              content="Show the next available sprite, including shiny or back views when available."
              position="bottom center"
              trigger={(
                <Button aria-label="Next sprite" icon onClick={showNextSprite} title="Next sprite">
                  <Icon name="angle right" />
                </Button>
              )}
            />
          </Button.Group>
        </Card.Content>
      ) : null}
    </Card>
  );
};

export { PokemonCard };
