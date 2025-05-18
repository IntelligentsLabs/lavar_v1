import express, { type Express, Router } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import { AirtableService } from "./services/airtable";
import { GoogleSheetsService } from "./services/google-sheets";
import { MakeService } from "./services/make";
import { z } from "zod";
import { 
  insertOAuthTokenSchema, 
  integrationConfigSchema, 
  integrations 
} from "@shared/schema";

// Create a Make.com service instance
const makeService = new MakeService();

export async function registerRoutes(app: Express): Promise<Server> {
  const apiRouter = Router();

  // Prefix all routes with /api
  app.use("/api", apiRouter);

// OAuth token exchange endpoint
apiRouter.post("/oauth/exchange", async (req, res) => {
  try {
    const { code, state, provider } = req.body;

    if (provider === 'google') {
      const oauthState = getOAuthState(state);

      if (!oauthState) {
        return res.status(400).json({ success: false, message: 'Invalid state parameter' });
      }

      const tokenResponse = await fetch('https://oauth2.googleapis.com/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: new URLSearchParams({
          client_id: process.env.GOOGLE_CLIENT_ID,
          client_secret: process.env.GOOGLE_CLIENT_SECRET,
          code,
          code_verifier: oauthState.codeVerifier,
          grant_type: 'authorization_code',
          redirect_uri: oauthState.redirectUri,
        }),
      });

      const tokenData = await tokenResponse.json();

      if (tokenData.error) {
        return res.status(400).json({ success: false, message: tokenData.error_description || 'Failed to exchange token' });
      }

      // Save token to your storage
      const token = await storage.saveOAuthToken({
        userId: 1, // Replace with actual user ID
        provider: 'google',
        accessToken: tokenData.access_token,
        refreshToken: tokenData.refresh_token,
        expiresAt: new Date(Date.now() + tokenData.expires_in * 1000),
      });

      return res.json({ success: true, token });
    }

    // Handle other providers...

  } catch (error) {
    console.error('Error exchanging OAuth token:', error);
    return res.status(500).json({ success: false, message: 'Server error exchanging token' });
  }
});

// OAuth logout endpoint - clear all or specific tokens for a user
  apiRouter.post("/oauth/logout", async (req, res) => {
    try {
      // For demo purposes, using a fixed user ID
      const userId = 1;
      const { provider } = req.query;

      if (provider && typeof provider === 'string') {
        console.log(`Logging out user ${userId}, clearing ${provider} token`);

        // Delete the specific token from storage
        if (provider === 'airtable' || provider === 'google') {
          const success = await storage.deleteOAuthToken(userId, provider);
          if (success) {
            console.log(`Successfully deleted ${provider} token for user ${userId}`);
          } else {
            console.log(`No ${provider} token found for user ${userId}`);
          }
        }
      } else {
        console.log(`Logging out user ${userId}, clearing all OAuth tokens`);
        // Delete both tokens
        await Promise.all([
          storage.deleteOAuthToken(userId, 'airtable'),
          storage.deleteOAuthToken(userId, 'google')
        ]);
      }

      res.json({ success: true, message: "Logged out successfully" });
    } catch (error) {
      console.error(`Error logging out:`, error);
      res.status(500).json({ 
        message: `Error logging out: ${error instanceof Error ? error.message : String(error)}` 
      });
    }
  });

  // Test API endpoint to verify Airtable connection
  apiRouter.get("/test/airtable/bases", async (req, res) => {
    try {
      const userId = 1; // Default user ID
      const token = await storage.getOAuthToken(userId, 'airtable');

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found. Please connect Airtable first." });
      }

      console.log("Fetching Airtable bases with token...");

      const { AirtableService } = await import('./services/airtable');
      const bases = await AirtableService.listBases(token);

      res.json({ 
        success: true,
        bases 
      });
    } catch (error) {
      console.error("Error listing Airtable bases:", error);
      res.status(500).json({ 
        message: "Failed to list Airtable bases", 
        error: error instanceof Error ? error.message : String(error) 
      });
    }
  });

  // Airtable API endpoints for integration setup
  apiRouter.get("/airtable/bases", async (req, res) => {
    try {
      const userId = 1; // Default user ID
      const token = await storage.getOAuthToken(userId, 'airtable');

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found. Please connect Airtable first." });
      }

      const { AirtableService } = await import('./services/airtable');
      const bases = await AirtableService.listBases(token);

      res.json({ bases });
    } catch (error) {
      console.error("Error listing Airtable bases:", error);
      res.status(500).json({ 
        message: "Failed to list Airtable bases", 
        error: error instanceof Error ? error.message : String(error) 
      });
    }
  });

  apiRouter.get("/airtable/bases/:baseId/tables", async (req, res) => {
    try {
      const { baseId } = req.params;
      const userId = 1; // Default user ID
      const token = await storage.getOAuthToken(userId, 'airtable');

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found. Please connect Airtable first." });
      }

      const { AirtableService } = await import('./services/airtable');
      const tables = await AirtableService.listTables(token, baseId);

      res.json({ tables });
    } catch (error) {
      console.error(`Error listing tables for base ${req.params.baseId}:`, error);
      res.status(500).json({ 
        message: "Failed to list Airtable tables", 
        error: error instanceof Error ? error.message : String(error) 
      });
    }
  });

  apiRouter.get("/airtable/bases/:baseId/tables/:tableId/fields", async (req, res) => {
    try {
      const { baseId, tableId } = req.params;
      const userId = 1; // Default user ID
      const token = await storage.getOAuthToken(userId, 'airtable');

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found. Please connect Airtable first." });
      }

      const { AirtableService } = await import('./services/airtable');
      const fields = await AirtableService.getTableFields(token, baseId, tableId);

      res.json({ fields });
    } catch (error) {
      console.error(`Error getting fields for table ${req.params.tableId}:`, error);
      res.status(500).json({ 
        message: "Failed to get Airtable fields", 
        error: error instanceof Error ? error.message : String(error) 
      });
    }
  });

  // Google Sheets API endpoints for integration setup
  apiRouter.get("/google/spreadsheets", async (req, res) => {
    try {
      const userId = 1; // Default user ID
      const token = await storage.getOAuthToken(userId, 'google');

      if (!token) {
        return res.status(401).json({ message: "Google token not found. Please connect Google Sheets first." });
      }

      const { GoogleSheetsService } = await import('./services/google-sheets');
      const spreadsheets = await GoogleSheetsService.listSpreadsheets(token);

      res.json({ spreadsheets });
    } catch (error) {
      console.error("Error listing Google spreadsheets:", error);
      res.status(500).json({ 
        message: "Failed to list Google spreadsheets", 
        error: error instanceof Error ? error.message : String(error) 
      });
    }
  });

  apiRouter.get("/google/spreadsheets/:spreadsheetId/sheets", async (req, res) => {
    try {
      const { spreadsheetId } = req.params;
      const userId = 1; // Default user ID
      const token = await storage.getOAuthToken(userId, 'google');

      if (!token) {
        return res.status(401).json({ message: "Google token not found. Please connect Google Sheets first." });
      }

      const { GoogleSheetsService } = await import('./services/google-sheets');
      const sheets = await GoogleSheetsService.listSheets(token, spreadsheetId);

      res.json({ sheets });
    } catch (error) {
      console.error(`Error listing sheets for spreadsheet ${req.params.spreadsheetId}:`, error);
      res.status(500).json({ 
        message: "Failed to list Google sheets", 
        error: error instanceof Error ? error.message : String(error) 
      });
    }
  });

  apiRouter.get("/google/spreadsheets/:spreadsheetId/sheets/:sheetName/headers", async (req, res) => {
    try {
      const { spreadsheetId, sheetName } = req.params;
      const userId = 1; // Default user ID
      const token = await storage.getOAuthToken(userId, 'google');

      if (!token) {
        return res.status(401).json({ message: "Google token not found. Please connect Google Sheets first." });
      }

      const { GoogleSheetsService } = await import('./services/google-sheets');
      const headers = await GoogleSheetsService.getSheetHeaders(token, spreadsheetId, sheetName);

      res.json({ headers });
    } catch (error) {
      console.error(`Error getting headers for sheet ${req.params.sheetName}:`, error);
      res.status(500).json({ 
        message: "Failed to get Google sheet headers", 
        error: error instanceof Error ? error.message : String(error) 
      });
    }
  });

  // OAuth token storage endpoint (for direct token storage if needed)
  apiRouter.post("/oauth/token", async (req, res) => {
    try {
      // Log the token request for debugging
      console.log("Received OAuth token request:", {
        provider: req.body.provider,
        userId: req.body.userId || 1
      });

      // Parse and validate the token data
      const tokenData = insertOAuthTokenSchema.parse({
        ...req.body,
        // Ensure userId is set to our default user if not provided
        userId: req.body.userId || 1
      });

      // Store the token
      const token = await storage.saveOAuthToken(tokenData);
      console.log(`OAuth token saved for provider ${token.provider} with ID ${token.id}`);

      res.json({
        success: true,
        token: {
          id: token.id,
          provider: token.provider
        }
      });
    } catch (error) {
      if (error instanceof z.ZodError) {
        console.error("OAuth token validation error:", error.errors);
        res.status(400).json({ 
          message: "Invalid token data", 
          errors: error.errors 
        });
      } else {
        console.error("Error saving OAuth token:", error);
        res.status(500).json({ message: "Failed to save OAuth token" });
      }
    }
  });

  // Get OAuth token endpoint
  apiRouter.get("/oauth/token", async (req, res) => {
    try {
      const { provider } = req.query;
      const userId = 1; // Use our default user

      if (!provider || typeof provider !== 'string') {
        return res.status(400).json({ message: "Provider is required" });
      }

      const token = await storage.getOAuthToken(userId, provider);

      if (!token) {
        return res.status(401).json({ message: `${provider} token not found` });
      }

      res.json({
        success: true,
        provider: token.provider,
        hasToken: true
      });
    } catch (error) {
      console.error("Error fetching OAuth token:", error);
      res.status(500).json({ message: "Failed to fetch OAuth token" });
    }
  });

  // Airtable endpoints
  apiRouter.get("/airtable/bases", async (req, res) => {
    try {
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "airtable");

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found" });
      }

      const bases = await AirtableService.listBases(token);
      res.json({ bases });
    } catch (error) {
      console.error("Error listing Airtable bases:", error);
      res.status(500).json({ message: "Failed to fetch Airtable bases" });
    }
  });

  apiRouter.get("/airtable/bases/:baseId/tables", async (req, res) => {
    try {
      const { baseId } = req.params;
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "airtable");

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found" });
      }

      const tables = await AirtableService.listTables(token, baseId);
      res.json({ tables });
    } catch (error) {
      console.error("Error listing Airtable tables:", error);
      res.status(500).json({ message: "Failed to fetch Airtable tables" });
    }
  });

  apiRouter.get("/airtable/bases/:baseId/tables/:tableId/fields", async (req, res) => {
    try {
      const { baseId, tableId } = req.params;
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "airtable");

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found" });
      }

      const fields = await AirtableService.getTableFields(token, baseId, tableId);
      res.json({ fields });
    } catch (error) {
      console.error("Error listing Airtable fields:", error);
      res.status(500).json({ message: "Failed to fetch Airtable fields" });
    }
  });

  apiRouter.post("/airtable/bases", async (req, res) => {
    try {
      const { name } = req.body;
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "airtable");

      if (!token) {
        return res.status(401).json({ message: "Airtable token not found" });
      }

      const base = await AirtableService.createBase(token, name);
      res.json({ base });
    } catch (error) {
      console.error("Error creating Airtable base:", error);
      res.status(500).json({ message: "Failed to create Airtable base" });
    }
  });

  // Google Sheets endpoints
  apiRouter.get("/google/spreadsheets", async (req, res) => {
    try {
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "google");

      if (!token) {
        return res.status(401).json({ message: "Google token not found" });
      }

      const spreadsheets = await GoogleSheetsService.listSpreadsheets(token);
      res.json({ spreadsheets });
    } catch (error) {
      console.error("Error listing Google Sheets:", error);
      res.status(500).json({ message: "Failed to fetch Google Sheets" });
    }
  });

  apiRouter.get("/google/spreadsheets/:spreadsheetId/sheets", async (req, res) => {
    try {
      const { spreadsheetId } = req.params;
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "google");

      if (!token) {
        return res.status(401).json({ message: "Google token not found" });
      }

      const sheets = await GoogleSheetsService.listSheets(token, spreadsheetId);
      res.json({ sheets });
    } catch (error) {
      console.error("Error listing Google Sheets:", error);
      res.status(500).json({ message: "Failed to fetch Google Sheets" });
    }
  });

  apiRouter.get("/google/spreadsheets/:spreadsheetId/sheets/:sheetName/headers", async (req, res) => {
    try {
      const { spreadsheetId, sheetName } = req.params;
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "google");

      if (!token) {
        return res.status(401).json({ message: "Google token not found" });
      }

      const headers = await GoogleSheetsService.getSheetHeaders(token, spreadsheetId, sheetName);
      res.json({ headers });
    } catch (error) {
      console.error("Error getting Google Sheet headers:", error);
      res.status(500).json({ message: "Failed to fetch Google Sheet headers" });
    }
  });

  apiRouter.post("/google/spreadsheets", async (req, res) => {
    try {
      const { name } = req.body;
      // In a real app, get userId from session
      const userId = 1; // Mock user ID
      const token = await storage.getOAuthToken(userId, "google");

      if (!token) {
        return res.status(401).json({ message: "Google token not found" });
      }

      const spreadsheet = await GoogleSheetsService.createSpreadsheet(token, name);
      res.json({ spreadsheet });
    } catch (error) {
      console.error("Error creating Google Sheet:", error);
      res.status(500).json({ message: "Failed to create Google Sheet" });
    }
  });

  // Integration endpoints
  apiRouter.post("/integrations", async (req, res) => {
    try {
      const configData = integrationConfigSchema.parse(req.body);

      // In a real app, get userId from session
      const userId = 1; // Mock user ID

      // Create or get resources as needed
      let airtableBaseId = configData.airtableBaseId;
      let airtableTableId = configData.airtableTableId;
      let googleSpreadsheetId = configData.googleSpreadsheetId;
      let googleSheetName = configData.googleSheetName;

      // Get tokens
      const airtableToken = await storage.getOAuthToken(userId, "airtable");
      const googleToken = await storage.getOAuthToken(userId, "google");

      if (!airtableToken || !googleToken) {
        return res.status(401).json({ 
          message: "Authentication tokens missing",
          airtableConnected: !!airtableToken,
          googleConnected: !!googleToken
        });
      }

      // Create Airtable base if requested
      if (configData.createNewAirtableBase) {
        const base = await AirtableService.createBase(airtableToken, `${configData.name} - Base`);
        airtableBaseId = base.id;
        airtableTableId = base.tables[0].id; // Use the first table
      }

      // Create Google Sheet if requested
      if (configData.createNewGoogleSheet) {
        const spreadsheet = await GoogleSheetsService.createSpreadsheet(
          googleToken, 
          `${configData.name} - Sheet`
        );
        googleSpreadsheetId = spreadsheet.spreadsheetId;
        googleSheetName = 'Synced Data'; // Default sheet name from the create function
      }

      // Create Make.com connections
      const airtableConnection = await makeService.createAirtableConnection(airtableToken);
      const googleConnection = await makeService.createGoogleSheetsConnection(googleToken);

      // Create integration record
      const integration = await storage.createIntegration({
        userId,
        name: configData.name,
        airtableBaseId,
        airtableTableId,
        googleSpreadsheetId,
        googleSheetName,
        fieldMappings: configData.fieldMappings,
        syncDirection: configData.syncDirection,
        syncFrequency: configData.syncFrequency,
        status: 'pending'
      });

      // Create Make.com scenario
      const scenario = await makeService.createScenario(
        integration,
        airtableConnection.id,
        googleConnection.id
      );

      // Update integration with scenario ID
      const updatedIntegration = await storage.updateIntegration(integration.id, {
        makeScenarioId: scenario.id,
        status: 'active'
      });

      res.json({ 
        success: true, 
        integration: updatedIntegration,
        scenario
      });
    } catch (error) {
      if (error instanceof z.ZodError) {
        res.status(400).json({ 
          message: "Invalid integration configuration", 
          errors: error.errors 
        });
      } else {
        console.error("Error creating integration:", error);
        res.status(500).json({ message: "Failed to create integration" });
      }
    }
  });

  apiRouter.get("/integrations", async (req, res) => {
    try {
      // In a real app, get userId from session
      const userId = 1; // Mock user ID

      const integrations = await storage.getIntegrationsByUserId(userId);
      res.json({ integrations });
    } catch (error) {
      console.error("Error fetching integrations:", error);
      res.status(500).json({ message: "Failed to fetch integrations" });
    }
  });

  apiRouter.get("/integrations/:id", async (req, res) => {
    try {
      const { id } = req.params;
      const integration = await storage.getIntegration(parseInt(id));

      if (!integration) {
        return res.status(404).json({ message: "Integration not found" });
      }

      res.json({ integration });
    } catch (error) {
      console.error("Error fetching integration:", error);
      res.status(500).json({ message: "Failed to fetch integration" });
    }
  });

  const httpServer = createServer(app);
  return httpServer;
}