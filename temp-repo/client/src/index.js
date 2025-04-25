import React from 'react';
import ReactDOM from 'react-dom/client'
import { Auth0Provider } from '@auth0/auth0-react';
import App from './App.jsx';
import './global.css'

const redirect = window.location.origin + '/authorize';
// render application
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>


    <Auth0Provider
        domain="dev-ly1qfq4ybnoqyrhp.us.auth0.com"
        clientId="BV0xRi79rcBK18MDAxrLTidbl8nkRfjJ"
        authorizationParams={{
          redirect_uri: redirect,
        }}
      >
        <App />
      </Auth0Provider>
    </React.StrictMode>
);
