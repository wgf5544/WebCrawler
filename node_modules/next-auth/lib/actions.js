import { Auth, raw, skipCSRFCheck } from "@auth/core";
import { headers as nextHeaders, cookies } from "next/headers";
import { redirect } from "next/navigation";
import { detectOrigin } from "./env.js";
export async function signIn(provider, options = {}, authorizationParams, config) {
    const headers = new Headers(nextHeaders());
    const { redirect: shouldRedirect = true, redirectTo, ...rest } = options instanceof FormData ? Object.fromEntries(options) : options;
    const callbackUrl = redirectTo?.toString() ?? headers.get("Referer") ?? "/";
    const base = authUrl(detectOrigin(headers), "signin");
    if (!provider) {
        const url = `${base}?${new URLSearchParams({ callbackUrl })}`;
        if (shouldRedirect)
            redirect(url);
        return url;
    }
    let url = `${base}/${provider}?${new URLSearchParams(authorizationParams)}`;
    let foundProvider = undefined;
    for (const _provider of config.providers) {
        const { id } = typeof _provider === "function" ? _provider?.() : _provider;
        if (id === provider) {
            foundProvider = id;
            break;
        }
    }
    if (!foundProvider) {
        const url = `${base}?${new URLSearchParams({ callbackUrl })}`;
        if (shouldRedirect)
            redirect(url);
        return url;
    }
    if (foundProvider === "credentials") {
        url = url.replace("signin", "callback");
    }
    headers.set("Content-Type", "application/x-www-form-urlencoded");
    const body = new URLSearchParams({ ...rest, callbackUrl });
    const req = new Request(url, { method: "POST", headers, body });
    const res = await Auth(req, { ...config, raw, skipCSRFCheck });
    for (const c of res?.cookies ?? [])
        cookies().set(c.name, c.value, c.options);
    if (shouldRedirect)
        return redirect(res.redirect);
    return res.redirect;
}
export async function signOut(options, config) {
    const headers = new Headers(nextHeaders());
    headers.set("Content-Type", "application/x-www-form-urlencoded");
    const url = authUrl(detectOrigin(headers), "signout");
    const callbackUrl = options?.redirectTo ?? headers.get("Referer") ?? "/";
    const body = new URLSearchParams({ callbackUrl });
    const req = new Request(url, { method: "POST", headers, body });
    const res = await Auth(req, { ...config, raw, skipCSRFCheck });
    for (const c of res?.cookies ?? [])
        cookies().set(c.name, c.value, c.options);
    if (options?.redirect ?? true)
        return redirect(res.redirect);
    return res;
}
export async function update(data, config) {
    const headers = new Headers(nextHeaders());
    headers.set("Content-Type", "application/json");
    const url = authUrl(detectOrigin(headers), "session");
    const body = JSON.stringify({ data });
    const req = new Request(url, { method: "POST", headers, body });
    const res = await Auth(req, { ...config, raw, skipCSRFCheck });
    for (const c of res?.cookies ?? [])
        cookies().set(c.name, c.value, c.options);
    return res.body;
}
/** Determine an action's URL */
function authUrl(base, action) {
    let pathname;
    if (base.pathname === "/")
        pathname ?? (pathname = `/api/auth/${action}`);
    else
        pathname ?? (pathname = `${base.pathname}/${action}`);
    return new URL(pathname, base.origin);
}
