import { NextRequest } from "next/server";
import type { headers } from "next/headers";
import type { NextAuthConfig } from "./index.js";
export declare function setEnvDefaults(config: NextAuthConfig): void;
/**
 * Extract the origin from `NEXTAUTH_URL` or `AUTH_URL`
 * environment variables, or the request's headers.
 */
export declare function detectOrigin(h: Headers | ReturnType<typeof headers>): URL;
/** If `NEXTAUTH_URL` or `AUTH_URL` is defined, override the request's URL. */
export declare function reqWithEnvUrl(req: NextRequest): NextRequest;
//# sourceMappingURL=env.d.ts.map