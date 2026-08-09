export const DEMO_SESSION_COOKIE = "sari_arta_demo_session";

type DemoAuthConfig = {
  email: string;
  password: string;
  secret: string;
};

export function getDemoAuthConfig(): DemoAuthConfig | null {
  if (process.env.APP_ENVIRONMENT !== "development") return null;
  const email = process.env.DEMO_AUTH_EMAIL?.trim().toLowerCase();
  const password = process.env.DEMO_AUTH_PASSWORD;
  const secret = process.env.DEMO_AUTH_SECRET;
  if (!email || !password || !secret || secret.length < 32) return null;
  return { email, password, secret };
}

export async function verifyDemoCredentials(
  email: string,
  password: string,
): Promise<boolean> {
  const config = getDemoAuthConfig();
  if (!config) return false;
  return constantTimeEqual(
    `${email.trim().toLowerCase()}\u0000${password}`,
    `${config.email}\u0000${config.password}`,
  );
}

export async function createDemoSessionToken(): Promise<string> {
  const config = getDemoAuthConfig();
  if (!config) throw new Error("Local demo authentication is not configured.");
  return sign(config.email, config.secret);
}

export async function verifyDemoSessionToken(
  token: string | undefined,
): Promise<boolean> {
  if (!token) return false;
  const config = getDemoAuthConfig();
  if (!config) return false;
  const expected = await sign(config.email, config.secret);
  return constantTimeEqual(token, expected);
}

async function sign(email: string, secret: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw",
    new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" },
    false,
    ["sign"],
  );
  const signature = await crypto.subtle.sign(
    "HMAC",
    key,
    new TextEncoder().encode(`sari-arta-demo:${email}`),
  );
  return toHex(new Uint8Array(signature));
}

async function constantTimeEqual(
  left: string,
  right: string,
): Promise<boolean> {
  const encoder = new TextEncoder();
  const [leftHash, rightHash] = await Promise.all([
    crypto.subtle.digest("SHA-256", encoder.encode(left)),
    crypto.subtle.digest("SHA-256", encoder.encode(right)),
  ]);
  const leftBytes = new Uint8Array(leftHash);
  const rightBytes = new Uint8Array(rightHash);
  let difference = 0;
  for (let index = 0; index < leftBytes.length; index += 1) {
    difference |= leftBytes[index] ^ rightBytes[index];
  }
  return difference === 0;
}

function toHex(bytes: Uint8Array): string {
  return Array.from(bytes, (byte) => byte.toString(16).padStart(2, "0")).join(
    "",
  );
}
