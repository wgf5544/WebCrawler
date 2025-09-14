import { z } from "zod";

// Auth configuration schema
export const authConfigSchema = z.object({
  secret: z.string().min(1),
  providers: z.array(z.string()).optional().default([]),
});

export type AuthConfig = z.infer<typeof authConfigSchema>;

// Default auth configuration
export const defaultAuthConfig: AuthConfig = {
  secret: process.env.NEXTAUTH_SECRET || "development-secret",
  providers: [],
};