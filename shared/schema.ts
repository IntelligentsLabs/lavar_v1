import { pgTable, text, serial, integer, boolean, json, timestamp } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: serial("id").primaryKey(),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

// OAuth tokens table
export const oauthTokens = pgTable("oauth_tokens", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id),
  provider: text("provider").notNull(), // 'airtable' or 'google'
  accessToken: text("access_token").notNull(),
  refreshToken: text("refresh_token"),
  expiresAt: timestamp("expires_at"),
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const insertOAuthTokenSchema = createInsertSchema(oauthTokens).omit({
  id: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertOAuthToken = z.infer<typeof insertOAuthTokenSchema>;
export type OAuthToken = typeof oauthTokens.$inferSelect;

// Integration configurations table
export const integrations = pgTable("integrations", {
  id: serial("id").primaryKey(),
  userId: integer("user_id").references(() => users.id),
  name: text("name").notNull(),
  airtableBaseId: text("airtable_base_id"),
  airtableTableId: text("airtable_table_id"),
  googleSpreadsheetId: text("google_spreadsheet_id"),
  googleSheetName: text("google_sheet_name"),
  fieldMappings: json("field_mappings").notNull(),
  syncDirection: text("sync_direction").notNull(), // 'airtable_to_google', 'google_to_airtable', 'bidirectional'
  syncFrequency: text("sync_frequency").notNull(), // 'realtime', 'hourly', 'daily', 'custom'
  makeScenarioId: text("make_scenario_id"),
  status: text("status").notNull(), // 'active', 'inactive', 'error'
  createdAt: timestamp("created_at").defaultNow(),
  updatedAt: timestamp("updated_at").defaultNow(),
});

export const insertIntegrationSchema = createInsertSchema(integrations).omit({
  id: true,
  makeScenarioId: true,
  createdAt: true,
  updatedAt: true,
});

export type InsertIntegration = z.infer<typeof insertIntegrationSchema>;
export type Integration = typeof integrations.$inferSelect;

// Field mapping schema for validation
export const fieldMappingSchema = z.object({
  airtableField: z.string(),
  googleSheetColumn: z.string(),
});

export type FieldMapping = z.infer<typeof fieldMappingSchema>;

// Integration configuration schema for API requests
export const integrationConfigSchema = z.object({
  name: z.string().min(1, "Name is required"),
  airtableBaseId: z.string().optional(),
  airtableTableId: z.string().optional(),
  googleSpreadsheetId: z.string().optional(),
  googleSheetName: z.string().optional(),
  createNewAirtableBase: z.boolean().optional(),
  createNewGoogleSheet: z.boolean().optional(),
  fieldMappings: z.array(fieldMappingSchema).min(1, "At least one field mapping is required"),
  syncDirection: z.enum(["airtable_to_google", "google_to_airtable", "bidirectional"]),
  syncFrequency: z.enum(["realtime", "hourly", "daily", "custom"]),
});

export type IntegrationConfig = z.infer<typeof integrationConfigSchema>;
