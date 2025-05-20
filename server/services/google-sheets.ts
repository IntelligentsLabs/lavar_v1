import { google } from 'googleapis';
import { OAuthToken } from '../../shared/schema';

export class GoogleSheetsService {
  static async getAuthClient(token: OAuthToken) {
    // Create OAuth2 client with the client credentials
    const clientId = process.env.VITE_GOOGLE_CLIENT_ID;
    const clientSecret = process.env.GOOGLE_CLIENT_SECRET;
    const redirectUri = 'https://66793246-3db9-4ceb-9826-7a03fb6463f5-00-tjsgi59cx3ud.worf.replit.dev:3001/auth/callback';

    if (!clientId || !clientSecret) {
      throw new Error('Missing Google client credentials');
    }
    
    const oauth2Client = new google.auth.OAuth2(clientId, clientSecret, redirectUri);
    oauth2Client.setCredentials({
      access_token: token.accessToken,
      refresh_token: token.refreshToken
    });

    // Refresh the token if needed
    oauth2Client.on('tokens', (tokens) => {
      if (tokens.refresh_token) {
        // Store the new refresh token if available
        token.refreshToken = tokens.refresh_token;
        storage.updateOAuthToken(token.id, { refreshToken: tokens.refresh_token });
      }
      token.accessToken = tokens.access_token;
      storage.updateOAuthToken(token.id, { accessToken: tokens.access_token });
    });

    return oauth2Client;
  }

// Add comprehensive error handling for API requests
const handleApiError = (error) => {
  console.error('API request error:', error);
  throw new Error(error?.response?.data?.error?.message || 'Failed API request');
};x

  static async listSpreadsheets(token: OAuthToken): Promise<any[]> {
    try {
      const auth = await this.getAuthClient(token);
      const drive = google.drive({ version: 'v3', auth });

      console.log('Fetching Google Sheets with Drive API...');

      // More comprehensive query to find all spreadsheets the user has access to
      const response = await drive.files.list({
        q: "mimeType='application/vnd.google-apps.spreadsheet'",
        fields: 'files(id, name)',
        spaces: 'drive',
        pageSize: 50,  // Fetch more spreadsheets
        orderBy: 'modifiedTime desc',  // Most recently modified first
        // Include files from shared drives and those shared with the user
        includeItemsFromAllDrives: true,
        supportsAllDrives: true
      });

      const files = response.data.files || [];
      console.log(`Found ${files.length} Google Sheets documents`);

      // If we didn't find any spreadsheets, try to create a sample one
      if (files.length === 0) {
        console.log('No spreadsheets found, attempting to create a sample one...');
        try {
          const newSpreadsheet = await this.createSpreadsheet(token, 'Sample Data Sync Spreadsheet');
          return [{ id: newSpreadsheet.spreadsheetId, name: newSpreadsheet.properties.title }];
        } catch (createError) {
          console.error('Error creating sample spreadsheet:', createError);
          // Continue without creating a spreadsheet
        }
      }

      return files;
    } catch (error) {
      console.error('Error listing Google Sheets:', error);
      throw error;
    }
  }

  static async getSpreadsheet(token: OAuthToken, spreadsheetId: string): Promise<any> {
    try {
      const auth = await this.getAuthClient(token);
      const sheets = google.sheets({ version: 'v4', auth });

      const response = await sheets.spreadsheets.get({
        spreadsheetId
      });

      return response.data;
    } catch (error) {
      console.error(`Error getting spreadsheet ${spreadsheetId}:`, error);
      throw error;
    }
  }

  static async listSheets(token: OAuthToken, spreadsheetId: string): Promise<any[]> {
    try {
      const spreadsheet = await this.getSpreadsheet(token, spreadsheetId);
      return spreadsheet.sheets.map((sheet: any) => ({
        id: sheet.properties.sheetId,
        name: sheet.properties.title
      }));
    } catch (error) {
      console.error(`Error listing sheets for spreadsheet ${spreadsheetId}:`, error);
      throw error;
    }
  }

  static async getSheetHeaders(token: OAuthToken, spreadsheetId: string, sheetName: string): Promise<string[]> {
    try {
      const auth = await this.getAuthClient(token);
      const sheets = google.sheets({ version: 'v4', auth });

      console.log(`Fetching headers for Google Sheet ${spreadsheetId}, sheet ${sheetName}...`);

      // First, check if there are existing headers
      const response = await sheets.spreadsheets.values.get({
        spreadsheetId,
        range: `${sheetName}!1:1`
      });

      // If we have headers, return them
      if (response.data.values && response.data.values.length > 0 && response.data.values[0].length > 0) {
        console.log(`Found ${response.data.values[0].length} headers in Google Sheet`);
        return response.data.values[0];
      }

      // If no headers found, create some default ones
      console.log('No headers found in sheet, creating default headers...');
      const defaultHeaders = ['ID', 'Name', 'Description', 'Status', 'Date', 'Notes'];

      try {
        // Add default headers to the sheet
        await sheets.spreadsheets.values.update({
          spreadsheetId,
          range: `${sheetName}!A1:F1`,
          valueInputOption: 'RAW',
          requestBody: {
            values: [defaultHeaders]
          }
        });

        console.log('Added default headers to sheet');
        return defaultHeaders;
      } catch (updateError) {
        console.error('Error adding default headers:', updateError);
        // If we can't update, still return the default headers
        return defaultHeaders;
      }
    } catch (error) {
      console.error(`Error getting headers for sheet ${sheetName}:`, error);
      // Return default headers even on error to allow the app to continue
      return ['Column A', 'Column B', 'Column C', 'Column D', 'Column E'];
    }
  }

  static async createSpreadsheet(token: OAuthToken, name: string): Promise<any> {
    try {
      const auth = await this.getAuthClient(token);
      const sheets = google.sheets({ version: 'v4', auth });

      const response = await sheets.spreadsheets.create({
        requestBody: {
          properties: {
            title: name
          },
          sheets: [
            {
              properties: {
                title: 'Synced Data',
                gridProperties: {
                  rowCount: 1000,
                  columnCount: 10
                }
              }
            }
          ]
        }
      });

      // Add headers to the sheet
      await sheets.spreadsheets.values.update({
        spreadsheetId: response.data.spreadsheetId,
        range: 'Synced Data!A1:E1',
        valueInputOption: 'RAW',
        requestBody: {
          values: [['ID', 'Name', 'Status', 'Date', 'Last Updated']]
        }
      });

      return response.data;
    } catch (error) {
      console.error('Error creating Google Sheet:', error);
      throw error;
    }
  }
}