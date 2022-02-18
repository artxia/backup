import { UpstreamOptions } from '../types/middlewares';

export const createResponse = (
  body: string,
  status: number,
): Response => new Response(body, {
  status,
});

export const getHostname = (
  request: Request,
): string => {
  const url = new URL(request.url);
  return url.host;
};

export const isSameOrigin = (
  url: URL,
  upstream: UpstreamOptions,
): boolean => {
  if (url.hostname !== upstream.domain) {
    return false;
  }

  if (url.port !== '') {
    return false;
  }

  if (
    upstream.protocol === undefined
    && url.protocol !== 'https:'
  ) {
    return false;
  }

  if (
    upstream.protocol !== undefined
    && `${upstream.protocol}:` !== url.protocol
  ) {
    return false;
  }
  return true;
};
