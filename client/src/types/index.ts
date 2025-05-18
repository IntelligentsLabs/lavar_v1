// Basic user type
export interface User {
  id: number;
  username: string;
}

// OAuth related types
export interface OAuthToken {
  id: number;
  userId: number;
  provider: string;
  accessToken: string;
  refreshToken?: string;
  expiresAt?: Date;
}

export interface OAuthState {
  provider: string;
  redirectUri: string;
  codeVerifier: string;
  state: string;
}

// Field mapping type
export interface FieldMapping {
  airtableField: string;
  googleSheetColumn: string;
}

// Airtable related types
export interface AirtableBase {
  id: string;
  name: string;
}

export interface AirtableTable {
  id: string;
  name: string;
}

export interface AirtableField {
  id: string;
  name: string;
  type: string;
}

// Google Sheets related types
export interface GoogleSpreadsheet {
  id: string;
  name: string;
}

export interface GoogleSheet {
  id: string;
  name: string;
}

// Integration related types
export interface IntegrationConfig {
  name: string;
  airtableBaseId?: string;
  airtableTableId?: string;
  googleSpreadsheetId?: string;
  googleSheetName?: string;
  createNewAirtableBase?: boolean;
  createNewGoogleSheet?: boolean;
  fieldMappings: FieldMapping[];
  syncDirection: 'airtable_to_google' | 'google_to_airtable' | 'bidirectional';
  syncFrequency: 'realtime' | 'hourly' | 'daily' | 'custom';
}

export interface Integration extends IntegrationConfig {
  id: number;
  userId: number;
  makeScenarioId?: string;
  status: 'pending' | 'active' | 'error';
  createdAt: Date;
  updatedAt: Date;
}

// Make.com related types
export interface MakeScenario {
  id: string;
  name: string;
  status: string;
}
