import React from "react";
import ReactDOM from "react-dom/client";
import { Auth0Provider } from "@auth0/auth0-react";
import App from "./App.jsx";
import "./global.css";
import { QueryClientProvider } from '@tanstack/react-query';
import { queryClient } from './lib/queryClient.ts';

const redirect = window.location.origin + "/authorize";
// render application
const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <Auth0Provider
      domain="dev-6xaas4zggao53u8z.us.auth0.com"
      clientId="KTdgNcNsJEGF1TIWvhGp2vEItWR0i9kb"
      authorizationParams={{
        redirect_uri: redirect,
      }}
    >
      <QueryClientProvider client={queryClient}>
        <App />
      </QueryClientProvider>
    </Auth0Provider>
  </React.StrictMode>,
);
