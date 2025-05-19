/// <reference types="vite/client" />

interface ImportMeta {
  readonly env: {
    readonly VITE_AIRTABLE_CLIENT_ID: string;
    readonly VITE_GOOGLE_CLIENT_ID: string;
    readonly [key: string]: any;
  }
}