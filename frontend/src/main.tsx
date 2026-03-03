import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';
import './index.css';
import './styles/animations.css';
import './styles/glass-physics.css';
import './styles/glassmorphism.css';

// React 19 Concurrent Features
const root = createRoot(document.getElementById('root')!, {
  onUncaughtError: (error) => {
    console.error('Uncaught error:', error);
  },
  onCaughtError: (error) => {
    console.error('Caught error:', error);
  }
});

root.render(
  <StrictMode>
    <App />
  </StrictMode>
);
