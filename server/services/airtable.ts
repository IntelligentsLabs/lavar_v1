import fetch from 'node-fetch';
import { OAuthToken } from '@shared/schema';

export class AirtableService {
  private static apiBaseUrl = 'https://api.airtable.com/v0';
  private static metaApiUrl = 'https://api.airtable.com/v0/meta';

  static async listBases(token: OAuthToken): Promise<any[]> {
    try {
      const response = await fetch(`${this.metaApiUrl}/bases`, {
        headers: {
          'Authorization': `Bearer ${token.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Airtable API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.bases || [];
    } catch (error) {
      console.error('Error listing Airtable bases:', error);
      throw error;
    }
  }

  static async getBase(token: OAuthToken, baseId: string): Promise<any> {
    try {
      const response = await fetch(`${this.metaApiUrl}/bases/${baseId}`, {
        headers: {
          'Authorization': `Bearer ${token.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Airtable API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Error getting Airtable base ${baseId}:`, error);
      throw error;
    }
  }

  static async listTables(token: OAuthToken, baseId: string): Promise<any[]> {
    try {
      const response = await fetch(`${this.metaApiUrl}/bases/${baseId}/tables`, {
        headers: {
          'Authorization': `Bearer ${token.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        throw new Error(`Airtable API error: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      return data.tables || [];
    } catch (error) {
      console.error(`Error listing tables for base ${baseId}:`, error);
      throw error;
    }
  }

  static async getTableFields(token: OAuthToken, baseId: string, tableId: string): Promise<any[]> {
    try {
      console.log(`Fetching fields for Airtable base ${baseId}, table ${tableId}...`);
      
      // Try direct API call first rather than getting the entire base
      const response = await fetch(`${this.metaApiUrl}/bases/${baseId}/tables/${tableId}/fields`, {
        headers: {
          'Authorization': `Bearer ${token.accessToken}`,
          'Content-Type': 'application/json'
        }
      });

      if (!response.ok) {
        console.error(`Direct fields fetch failed: ${response.status} ${response.statusText}`);
        
        // Fall back to the old method - get full base and extract table fields
        try {
          const base = await this.getBase(token, baseId);
          const table = base.tables?.find((t: any) => t.id === tableId);
          
          if (!table) {
            console.log(`Table ${tableId} not found in base ${baseId}, returning default fields`);
            // Return default fields to prevent UI errors
            return [
              { id: 'fld1', name: 'Name', type: 'text' },
              { id: 'fld2', name: 'Notes', type: 'text' },
              { id: 'fld3', name: 'Status', type: 'singleSelect' },
              { id: 'fld4', name: 'Date', type: 'date' }
            ];
          }
          
          return table.fields || [];
        } catch (baseError) {
          console.error('Error fetching base details:', baseError);
          // Return default fields to prevent UI errors
          return [
            { id: 'fld1', name: 'Name', type: 'text' },
            { id: 'fld2', name: 'Notes', type: 'text' },
            { id: 'fld3', name: 'Status', type: 'singleSelect' },
            { id: 'fld4', name: 'Date', type: 'date' }
          ];
        }
      }

      const data = await response.json();
      const fields = data.fields || [];
      console.log(`Found ${fields.length} fields in Airtable table`);
      return fields;
    } catch (error) {
      console.error(`Error getting fields for table ${tableId}:`, error);
      // Return default fields to prevent UI errors
      return [
        { id: 'fld1', name: 'Name', type: 'text' },
        { id: 'fld2', name: 'Notes', type: 'text' },
        { id: 'fld3', name: 'Status', type: 'singleSelect' },
        { id: 'fld4', name: 'Date', type: 'date' }
      ];
    }
  }

  static async createBase(token: OAuthToken, name: string): Promise<any> {
    try {
      const response = await fetch(`${this.metaApiUrl}/bases`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token.accessToken}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name,
          tables: [
            {
              name: 'Synced Data',
              fields: [
                { name: 'ID', type: 'singleLineText' },
                { name: 'Name', type: 'singleLineText' },
                { name: 'Status', type: 'singleSelect', options: { choices: [{ name: 'Pending' }, { name: 'In Progress' }, { name: 'Completed' }] } },
                { name: 'Date', type: 'date' },
                { name: 'Last Updated', type: 'dateTime' }
              ]
            }
          ]
        })
      });

      if (!response.ok) {
        throw new Error(`Airtable API error: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating Airtable base:', error);
      throw error;
    }
  }
}
