import { 
  users, type User, type InsertUser,
  oauthTokens, type OAuthToken, type InsertOAuthToken,
  integrations, type Integration, type InsertIntegration
} from "../shared/schema";
import { db } from "./db";
import { eq, and } from "drizzle-orm";
import { IStorage } from "./storage";

export class DatabaseStorage implements IStorage {
  // User operations
  async getUser(id: number): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.id, id));
    return user;
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const [user] = await db.select().from(users).where(eq(users.username, username));
    return user;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    // Check if the user already exists first
    const existingUser = await this.getUserByUsername(insertUser.username);
    if (existingUser) {
      return existingUser;
    }

    // Create a new user if one doesn't exist
    const [user] = await db
      .insert(users)
      .values(insertUser)
      .returning();
    return user;
  }

  // OAuth tokens operations
  async getOAuthToken(userId: number, provider: string): Promise<OAuthToken | undefined> {
    // Ensure we're always working with a valid userId
    if (!userId) {
      console.warn(`Invalid userId: ${userId}, defaulting to 1`);
      userId = 1;
    }

    try {
      const [token] = await db
        .select()
        .from(oauthTokens)
        .where(
          and(
            eq(oauthTokens.userId, userId),
            eq(oauthTokens.provider, provider)
          )
        );
      return token;
    } catch (error) {
      console.error(`Error getting OAuth token for userId ${userId} and provider ${provider}:`, error);
      return undefined;
    }
  }

  async saveOAuthToken(insertToken: InsertOAuthToken): Promise<OAuthToken> {
    // Ensure we have a valid userId
    const userId = insertToken.userId ?? 1; // Default to user ID 1 if not provided

    // Check if token exists for this user and provider
    const existingToken = await this.getOAuthToken(userId, insertToken.provider);

    if (existingToken) {
      // Update existing token
      const updatedToken = await this.updateOAuthToken(existingToken.id, insertToken);
      if (!updatedToken) {
        throw new Error('Failed to update existing token');
      }
      return updatedToken;
    }

    // Prepare token data with nulls for optional fields
    const tokenData = {
      ...insertToken,
      userId: userId,
      refreshToken: insertToken.refreshToken ?? null,
      expiresAt: insertToken.expiresAt ?? null
    };

    // Create new token
    const [token] = await db
      .insert(oauthTokens)
      .values(tokenData)
      .returning();
    return token;
  }

  async updateOAuthToken(id: number, tokenUpdate: Partial<InsertOAuthToken>): Promise<OAuthToken | undefined> {
    // Ensure userId is always a number
    const safeUpdate = {
      ...tokenUpdate,
      userId: tokenUpdate.userId ?? null,
      updatedAt: new Date()
    };

    const [updatedToken] = await db
      .update(oauthTokens)
      .set(safeUpdate)
      .where(eq(oauthTokens.id, id))
      .returning();

    return updatedToken;
  }

  async deleteOAuthToken(userId: number, provider: string): Promise<boolean> {
    try {
      await db
        .delete(oauthTokens)
        .where(
          and(
            eq(oauthTokens.userId, userId),
            eq(oauthTokens.provider, provider)
          )
        );
      return true;
    } catch (error) {
      console.error(`Error deleting OAuth token for userId ${userId} and provider ${provider}:`, error);
      return false;
    }
  }

  // Integration operations
  async getIntegration(id: number): Promise<Integration | undefined> {
    const [integration] = await db
      .select()
      .from(integrations)
      .where(eq(integrations.id, id));
    return integration;
  }

  async getIntegrationsByUserId(userId: number): Promise<Integration[]> {
    return db
      .select()
      .from(integrations)
      .where(eq(integrations.userId, userId));
  }

  async createIntegration(insertIntegration: InsertIntegration): Promise<Integration> {
    // Ensure we have a valid userId
    const userId = insertIntegration.userId ?? 1;

    // Prepare integration data with nulls for optional fields
    const integrationData = {
      ...insertIntegration,
      userId: userId,
      airtableBaseId: insertIntegration.airtableBaseId ?? null,
      airtableTableId: insertIntegration.airtableTableId ?? null,
      googleSpreadsheetId: insertIntegration.googleSpreadsheetId ?? null,
      googleSheetName: insertIntegration.googleSheetName ?? null,
      makeScenarioId: null, // Initialize as null, will be updated later
      status: insertIntegration.status || 'pending'
    };

    const [integration] = await db
      .insert(integrations)
      .values(integrationData)
      .returning();

    return integration;
  }

  async updateIntegration(id: number, integrationUpdate: Partial<InsertIntegration>): Promise<Integration | undefined> {
    // Ensure all nullable fields are properly handled
    const safeUpdate = {
      ...integrationUpdate,
      userId: integrationUpdate.userId ?? undefined,
      airtableBaseId: integrationUpdate.airtableBaseId ?? undefined,
      airtableTableId: integrationUpdate.airtableTableId ?? undefined,
      googleSpreadsheetId: integrationUpdate.googleSpreadsheetId ?? undefined,
      googleSheetName: integrationUpdate.googleSheetName ?? undefined,
      updatedAt: new Date()
    };

    const [updatedIntegration] = await db
      .update(integrations)
      .set(safeUpdate)
      .where(eq(integrations.id, id))
      .returning();

    return updatedIntegration;
  }
}