import { 
  users, type User, type InsertUser,
  oauthTokens, type OAuthToken, type InsertOAuthToken,
  integrations, type Integration, type InsertIntegration
} from "../shared/schema";

// Interface for all storage operations
export interface IStorage {
  // User operations
  getUser(id: number): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;
  
  // OAuth tokens operations
  getOAuthToken(userId: number, provider: string): Promise<OAuthToken | undefined>;
  saveOAuthToken(token: InsertOAuthToken): Promise<OAuthToken>;
  updateOAuthToken(id: number, token: Partial<InsertOAuthToken>): Promise<OAuthToken | undefined>;
  deleteOAuthToken(userId: number, provider: string): Promise<boolean>;
  
  // Integration operations
  getIntegration(id: number): Promise<Integration | undefined>;
  getIntegrationsByUserId(userId: number): Promise<Integration[]>;
  createIntegration(integration: InsertIntegration): Promise<Integration>;
  updateIntegration(id: number, integration: Partial<InsertIntegration>): Promise<Integration | undefined>;
}

export class MemStorage implements IStorage {
  private users: Map<number, User>;
  private oauthTokens: Map<number, OAuthToken>;
  private integrations: Map<number, Integration>;
  currentUserId: number;
  currentTokenId: number;
  currentIntegrationId: number;

  constructor() {
    this.users = new Map();
    this.oauthTokens = new Map();
    this.integrations = new Map();
    this.currentUserId = 1;
    this.currentTokenId = 1;
    this.currentIntegrationId = 1;
  }

  // User operations
  async getUser(id: number): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find(
      (user) => user.username === username,
    );
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = this.currentUserId++;
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  // OAuth tokens operations
  async getOAuthToken(userId: number, provider: string): Promise<OAuthToken | undefined> {
    return Array.from(this.oauthTokens.values()).find(
      (token) => token.userId === userId && token.provider === provider
    );
  }

  async saveOAuthToken(insertToken: InsertOAuthToken): Promise<OAuthToken> {
    // Check if token exists for this user and provider
    const existingToken = await this.getOAuthToken(insertToken.userId, insertToken.provider);
    
    if (existingToken) {
      // Update existing token
      return this.updateOAuthToken(existingToken.id, insertToken) as Promise<OAuthToken>;
    }
    
    // Create new token
    const id = this.currentTokenId++;
    const now = new Date();
    const token: OAuthToken = { 
      ...insertToken, 
      id, 
      createdAt: now, 
      updatedAt: now 
    };
    this.oauthTokens.set(id, token);
    return token;
  }

  async updateOAuthToken(id: number, tokenUpdate: Partial<InsertOAuthToken>): Promise<OAuthToken | undefined> {
    const existingToken = this.oauthTokens.get(id);
    
    if (!existingToken) {
      return undefined;
    }
    
    const updatedToken: OAuthToken = {
      ...existingToken,
      ...tokenUpdate,
      updatedAt: new Date()
    };
    
    this.oauthTokens.set(id, updatedToken);
    return updatedToken;
  }
  
  async deleteOAuthToken(userId: number, provider: string): Promise<boolean> {
    try {
      // Find the token with matching userId and provider
      let tokenIdToDelete: number | null = null;
      for (const [id, token] of this.oauthTokens.entries()) {
        if (token.userId === userId && token.provider === provider) {
          tokenIdToDelete = id;
          break;
        }
      }
      
      // Delete the token if found
      if (tokenIdToDelete !== null) {
        this.oauthTokens.delete(tokenIdToDelete);
        return true;
      }
      
      return false;
    } catch (error) {
      console.error(`Error deleting OAuth token for userId ${userId} and provider ${provider}:`, error);
      return false;
    }
  }

  // Integration operations
  async getIntegration(id: number): Promise<Integration | undefined> {
    return this.integrations.get(id);
  }

  async getIntegrationsByUserId(userId: number): Promise<Integration[]> {
    return Array.from(this.integrations.values()).filter(
      (integration) => integration.userId === userId
    );
  }

  async createIntegration(insertIntegration: InsertIntegration): Promise<Integration> {
    const id = this.currentIntegrationId++;
    const now = new Date();
    const integration: Integration = {
      ...insertIntegration,
      id,
      createdAt: now,
      updatedAt: now
    };
    
    this.integrations.set(id, integration);
    return integration;
  }

  async updateIntegration(id: number, integrationUpdate: Partial<InsertIntegration>): Promise<Integration | undefined> {
    const existingIntegration = this.integrations.get(id);
    
    if (!existingIntegration) {
      return undefined;
    }
    
    const updatedIntegration: Integration = {
      ...existingIntegration,
      ...integrationUpdate,
      updatedAt: new Date()
    };
    
    this.integrations.set(id, updatedIntegration);
    return updatedIntegration;
  }
}

// Import DatabaseStorage
import { DatabaseStorage } from "./database-storage";

// Use DatabaseStorage instead of MemStorage
export const storage = new DatabaseStorage();
