export const dynamic = "force-dynamic";
export const revalidate = 0;

function jsonResponse(body: unknown, status: number) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}
/**
 * Server-side proxy to the Gloria API.
 * Keeps the API key on the server, never in the browser bundle.
 */
export async function POST(req: Request) {
  const env = (globalThis as typeof globalThis & {
    process?: { env?: Record<string, string | undefined> };
  }).process?.env;
  const apiUrl = env?.GLORIA_API_URL;
  const apiKey = env?.GLORIA_API_KEY;

  if (!apiUrl || !apiKey) {
    return jsonResponse(
      { error: 'GLORIA_API_URL or GLORIA_API_KEY is not set on the server.' },
      500,
    );
  }

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return jsonResponse({ error: 'Invalid JSON body.' }, 400);
  }

  try {
    const upstream = await fetch(`${apiUrl.replace(/\/$/, '')}/v1/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${apiKey}`,
      },
      body: JSON.stringify(body),
      cache: 'no-store',
    });

    const text = await upstream.text();
    return new Response(text, {
      status: upstream.status,
      headers: {
        'Content-Type':
          upstream.headers.get('content-type') ?? 'application/json',
      },
    });
  } catch (err) {
    return jsonResponse(
      { error: `Upstream request failed: ${(err as Error).message}` },
      502,
    );
  }
}
