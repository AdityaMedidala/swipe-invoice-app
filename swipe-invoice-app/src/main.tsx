import React from 'react';
import ReactDOM from 'react-dom/client';

import { Provider } from 'react-redux';
import { store } from './app/store';

import App from './App';

import '@mantine/core/styles.css';
import '@mantine/dates/styles.css'; // Added for date picker support
import '@mantine/dropzone/styles.css';
import 'mantine-react-table/styles.css'; // Added for Table support

ReactDOM.createRoot(
  document.getElementById('root')!
).render(
  <React.StrictMode>
    <Provider store={store}>
      <App />
    </Provider>
  </React.StrictMode>
);
