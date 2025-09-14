import { z } from "zod";
export declare const authConfigSchema: z.ZodObject<{
    secret: z.ZodString;
    providers: z.ZodDefault<z.ZodOptional<z.ZodArray<z.ZodString, "many">>>;
}, "strip", z.ZodTypeAny, {
    secret: string;
    providers: string[];
}, {
    secret: string;
    providers?: string[] | undefined;
}>;
export type AuthConfig = z.infer<typeof authConfigSchema>;
export declare const defaultAuthConfig: AuthConfig;
