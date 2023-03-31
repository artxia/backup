import { Middleware } from '../../types/middleware';

export const setForwardedHeaders = (
  headers: Headers,
): void => {
  headers.set('X-Forwarded-Proto', 'https');

  const host = headers.get('Host');
  if (host !== null) {
    headers.set('X-Forwarded-Host', host);
  }

  const ip = headers.get('cf-connecting-ip');
  const forwardedForHeader = headers.get('X-Forwarded-For');
  if (ip !== null && forwardedForHeader === null) {
    headers.set('X-Forwarded-For', ip);
  }
};

/**
 * The `useHeaders` middleware modifies the headers of the request and response.
 * - The middleware adds `X-Forwarded-Proto`, `X-Forwarded-For`, and
 * `X-Forwarded-Host` headers to indicate that the client is connecting to the
 * upstream through a reverse proxy.
 * - The middleware adds customized headers to the request and response.
 * @param context - The context of the middleware pipeline
 * @param next - The function to invoke the next middleware in the pipeline
 */
export const useHeaders: Middleware = async (
  context,
  next,
) => {
  const { request, route } = context;

  const requestHeaders = new Headers(request.headers);
  setForwardedHeaders(requestHeaders);

  if (route.headers === undefined) {
    context.request = new Request(request.url, {
      body: request.body,
      method: request.method,
      headers: requestHeaders,
    });
    await next();
    return;
  }

  if (route.headers.request !== undefined) {
    for (const [key, value] of Object.entries(route.headers.request)) {
      if (value.length === 0) {
        requestHeaders.delete(key);
      } else {
        requestHeaders.set(key, value);
      }
    }
  }

  context.request = new Request(request.url, {
    body: request.body,
    method: request.method,
    headers: requestHeaders,
  });

  await next();

  const { response } = context;
  const responseHeaders = new Headers(response.headers);

  if (route.headers.response !== undefined) {
    for (const [key, value] of Object.entries(route.headers.response)) {
      if (value.length === 0) {
        responseHeaders.delete(key);
      } else {
        responseHeaders.set(key, value);
      }
    }
  }

  context.response = new Response(
    response.body,
    {
      status: response.status,
      statusText: response.statusText,
      headers: responseHeaders,
    },
  );
};
