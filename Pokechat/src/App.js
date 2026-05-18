import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./pages/Layout";
import Home from './pages/Home';
import {PokemonChat} from './pages/PokemonChat';
import {PokemonCardBrowser} from './pages/PokemonCardBrowser';


import './App.scss';
import 'semantic-ui-css/semantic.min.css'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index path="/" element={<Home />} />
          <Route path="/card" element={<PokemonCardBrowser />} />
          <Route path="/chat" element={<PokemonChat />} />
          
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
