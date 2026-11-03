import React from 'react';
import ReactDOM from 'react-dom/client';
import { Toaster } from 'react-hot-toast';
import App from './App';
import './index.css';

ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
    <Toaster position="top-right" toastOptions={{
      duration: 3500,
      style: { borderRadius: '12px', background: '#0f172a', color: '#fff', fontSize: '13px' },
    }} />
  </React.StrictMode>,
);
