import { z } from "zod";
// Auth configuration schema
export const authConfigSchema = z.object({
    secret: z.string().min(1),
    providers: z.array(z.string()).optional().default([]),
});
// Default auth configuration
export const defaultAuthConfig = {
    secret: process.env.NEXTAUTH_SECRET || "development-secret",
    providers: [],
};
