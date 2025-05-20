import fetch from 'node-fetch';
import { OAuthToken, Integration, FieldMapping } from '../../shared/schema';

export class MakeService {
  private static apiUrl = 'https://eu1.make.com/api/v2';
  private apiKey: string;

  constructor() {
    // Get Make.com API key from environment variables
    this.apiKey = process.env.MAKE_API_KEY || '';

    if (!this.apiKey) {
      console.warn('Make.com API key not found. Make API calls will fail.');
    }
  }

  private async makeRequest(method: string, endpoint: string, data?: any) {
    try {
      const url = `${MakeService.apiUrl}${endpoint}`;
      const options: any = {
        method,
        headers: {
          'Authorization': `Token ${this.apiKey}`,
          'Content-Type': 'application/json'
        }
      };

      if (data) {
        options.body = JSON.stringify(data);
      }

      const response = await fetch(url, options);

      if (!response.ok) {
        const errorText = await response.text();
        throw new Error(`Make.com API error: ${response.status} ${response.statusText} - ${errorText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Error in Make.com API request to ${endpoint}:`, error);
      throw error;
    }
  }

  async createAirtableConnection(token: OAuthToken): Promise<any> {
    return this.makeRequest('POST', '/connections', {
      name: 'Airtable Connection via Integration Hub',
      type: 'airtable',
      authorization: {
        type: 'oauth2',
        token: {
          access_token: token.accessToken,
          refresh_token: token.refreshToken,
          expires_in: token.expiresAt ? new Date(token.expiresAt).getTime() - Date.now() : 3600
        }
      }
    });
  }

  async createGoogleSheetsConnection(token: OAuthToken): Promise<any> {
    return this.makeRequest('POST', '/connections', {
      name: 'Google Sheets Connection via Integration Hub',
      type: 'google-sheets',
      authorization: {
        type: 'oauth2',
        token: {
          access_token: token.accessToken,
          refresh_token: token.refreshToken,
          expires_in: token.expiresAt ? new Date(token.expiresAt).getTime() - Date.now() : 3600
        }
      }
    });
  }

  async createScenario(
    integration: Integration, 
    airtableConnectionId: string, 
    googleConnectionId: string
  ): Promise<any> {
    // Create the scenario
    const scenario = await this.makeRequest('POST', '/scenarios', {
      name: integration.name || 'Airtable to Google Sheets Sync',
      folderID: '0', // Default folder
      blueprint: false // Not using a blueprint
    });

    // Configure the modules based on sync direction
    let modules = [];
    let mappings = [];

    // Parse the field mappings from JSON
    const fieldMappings = integration.fieldMappings as unknown as FieldMapping[];

    if (integration.syncDirection === 'airtable_to_google' || integration.syncDirection === 'bidirectional') {
      // Add Airtable trigger module first
      modules.push({
        name: 'Airtable Watch Records',
        type: 'airtable',
        connection: airtableConnectionId,
        operation: 'watchRecords',
        parameters: {
          baseId: integration.airtableBaseId,
          tableId: integration.airtableTableId
        }
      });

      // Add Google Sheets action module
      modules.push({
        name: 'Google Sheets Add/Update Row',
        type: 'google-sheets',
        connection: googleConnectionId,
        operation: 'addUpdateRow',
        parameters: {
          spreadsheetId: integration.googleSpreadsheetId,
          sheetName: integration.googleSheetName,
          // Configure the column mapping based on field mappings
          columnMapping: fieldMappings.reduce((mapping, field) => {
            mapping[field.googleSheetColumn] = `{{1.${field.airtableField}}}`;
            return mapping;
          }, {} as Record<string, string>)
        }
      });

      // Connect modules
      mappings.push({
        from: 1, // Module 1 (Airtable)
        to: 2    // Module 2 (Google Sheets)
      });
    }

    if (integration.syncDirection === 'google_to_airtable' || integration.syncDirection === 'bidirectional') {
      // For Google to Airtable direction, add appropriate modules
      const startIndex = modules.length + 1;

      // Add Google Sheets trigger module
      modules.push({
        name: 'Google Sheets Watch Rows',
        type: 'google-sheets',
        connection: googleConnectionId,
        operation: 'watchRows',
        parameters: {
          spreadsheetId: integration.googleSpreadsheetId,
          sheetName: integration.googleSheetName
        }
      });

      // Add Airtable action module
      modules.push({
        name: 'Airtable Create/Update Record',
        type: 'airtable',
        connection: airtableConnectionId,
        operation: 'createUpdateRecord',
        parameters: {
          baseId: integration.airtableBaseId,
          tableId: integration.airtableTableId,
          // Configure the field mapping based on field mappings
          fieldMapping: fieldMappings.reduce((mapping, field) => {
            mapping[field.airtableField] = `{{${startIndex}.${field.googleSheetColumn}}}`;
            return mapping;
          }, {} as Record<string, string>)
        }
      });

      // Connect modules
      mappings.push({
        from: startIndex,     // Google Sheets module
        to: startIndex + 1    // Airtable module
      });
    }

    // Add modules to the scenario
    await this.makeRequest('POST', `/scenarios/${scenario.id}/modules`, { modules });

    // Add connections between modules
    await this.makeRequest('POST', `/scenarios/${scenario.id}/connections`, { mappings });

    // Configure scenario scheduling based on syncFrequency
    let scheduling = {};

    switch (integration.syncFrequency) {
      case 'realtime':
        scheduling = { type: 'realtime' };
        break;
      case 'hourly':
        scheduling = { type: 'interval', interval: { unit: 'hours', value: 1 } };
        break;
      case 'daily':
        scheduling = { type: 'interval', interval: { unit: 'days', value: 1 } };
        break;
      case 'custom':
        scheduling = { type: 'advanced', cron: '0 0 * * *' }; // Default to midnight
        break;
    }

    await this.makeRequest('PATCH', `/scenarios/${scenario.id}`, { scheduling });

    // Activate the scenario
    await this.makeRequest('POST', `/scenarios/${scenario.id}/activate`);

    return scenario;
  }

  async getScenario(scenarioId: string): Promise<any> {
    return this.makeRequest('GET', `/scenarios/${scenarioId}`);
  }
}
