/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_AIRTABLE_CLIENT_ID: string;
  readonly VITE_GOOGLE_CLIENT_ID: string;
  // Add any other environment variables your app needs here
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}