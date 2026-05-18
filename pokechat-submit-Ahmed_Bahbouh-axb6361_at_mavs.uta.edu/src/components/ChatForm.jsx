import React, { useState } from 'react';
import { Button, Icon, Input, Loader, Message, Popup } from 'semantic-ui-react';
import axios from 'axios';
import { CHAT_API } from '../AppConfig';

const PROMPT_OPTIONS = [
  { color: 'red', label: 'Strongest Pokemon', message: 'strongest pokemon limit 1' },
  { color: 'blue', label: 'Weakest Pokemon', message: 'weakest pokemon limit 1' },
  { color: 'green', label: 'Starter Pokemon', message: 'starter pokemon limit 3' },
];

const normalizePokemonResults = (payload) => {
  const rawItems = Array.isArray(payload) ? payload : [payload];

  return [...new Set(
    rawItems
      .map((item) => {
        if (!item) {
          return null;
        }

        if (typeof item === 'number') {
          return item;
        }

        if (typeof item === 'string') {
          return item.trim();
        }

        if (typeof item === 'object') {
          return item.id || item.name || item.pokemon?.id || item.pokemon?.name || null;
        }

        return null;
      })
      .filter(Boolean),
  )];
};

// HANDLES INTERACTIONS WITH THE LLM (/backend)
const ChatForm = ({
  setSearchResults,
  setIsLoading: setParentLoading = () => {},
  setErrorMessage: setParentError = () => {},
  setActiveQuery: setParentActiveQuery = () => {},
}) => {
  const [queryText, setQueryText] = useState('');
  const [activeQuery, setActiveQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const chat = (query) => {
    if (isLoading) {
      return;
    }

    const nextQuery = query.trim();

    if (!nextQuery) {
      setError('Enter a Pokemon question before sending.');
      setParentError('Enter a Pokemon question before sending.');
      return;
    }

    setActiveQuery(nextQuery);
    setParentActiveQuery(nextQuery);
    setError('');
    setIsLoading(true);
    setParentLoading(true);
    setParentError('');
    setSearchResults([]);

    axios
      .get(`${CHAT_API}/chat/query`, {
        params: { q: nextQuery },
      })
      .then((response) => {
        if (response.data?.error) {
          throw new Error(response.data.error);
        }

        const pokemonResults = normalizePokemonResults(response.data);

        if (pokemonResults.length === 0) {
          throw new Error('The model did not return any Pokemon results for that prompt.');
        }

        setSearchResults(pokemonResults);
      })
      .catch((err) => {
        setSearchResults([]);
        const message = err.message || 'Unable to reach the PokeChat API.';
        setError(message);
        setParentError(message);
      })
      .finally(() => {
        setIsLoading(false);
        setParentLoading(false);
      });
  };

  const sendActiveInput = () => {
    chat(queryText);
  };

  const onExampleClick = (message) => {
    setQueryText(message);
    chat(message);
  };

  const clearChat = () => {
    if (isLoading) {
      return;
    }

    setQueryText('');
    setActiveQuery('');
    setParentActiveQuery('');
    setError('');
    setParentError('');
    setSearchResults([]);
  };

  const onInputKeyDown = (event) => {
    if (event.key === 'Enter') {
      sendActiveInput();
    }
  };
  const canSend = queryText.trim().length > 0;

  return (
    <div>
      <Input
        action={{
          color: 'blue',
          content: isLoading ? 'Sending' : 'Send',
          icon: 'send',
          onClick: sendActiveInput,
          disabled: isLoading || !canSend,
          title: canSend ? 'Send this Pokemon question' : 'Type a question or use a suggestion first',
        }}
        aria-label="Pokemon chat query"
        disabled={isLoading}
        fluid
        onChange={(event, { value }) => {
          setQueryText(value);
          if (error) {
            setError('');
            setParentError('');
          }
        }}
        onKeyDown={onInputKeyDown}
        placeholder="Try: best fire dragon limit 2"
        value={queryText}
      />
      <div className="suggested-prompts">
        {PROMPT_OPTIONS.map((prompt) => (
          <Popup
            content={`Search for "${prompt.message}" and show matching Pokemon cards.`}
            key={prompt.message}
            position="bottom center"
            trigger={(
              <Button
                basic={activeQuery !== prompt.message}
                color={prompt.color}
                disabled={isLoading}
                onClick={() => onExampleClick(prompt.message)}
                title={`Search: ${prompt.message}`}
              >
                {prompt.label}
              </Button>
            )}
          />
        ))}
        <Popup
          content="Reset the prompt, status, errors, and returned cards."
          position="bottom center"
          trigger={(
            <Button basic disabled={isLoading} icon labelPosition="left" onClick={clearChat} title="Clear prompt and results">
              <Icon name="erase" />
              Clear
            </Button>
          )}
        />
      </div>
      {isLoading ? <Loader active inline="centered" content={`Loading cards for: ${activeQuery}`} /> : null}
      {error ? (
        <Message aria-live="assertive" negative size="small" style={{ marginTop: '0.75em' }}>
          <Message.Header>Chat request failed</Message.Header>
          <p>{error}</p>
        </Message>
      ) : null}
    </div>
  );
};

export { ChatForm };
