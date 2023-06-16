import { Middleware } from '../../types/middleware';
import { UpstreamOptions } from '../../types/middlewares/upstream';
import { castToIterable } from '../utils';

export const rewriteURL = (
  url: string,
  upstream: UpstreamOptions,
): string => {
  const cloneURL = new URL(url);
  const {
    domain,
    port,
    protocol,
  } = upstream;

  cloneURL.hostname = domain;

  if (protocol !== undefined) {
    cloneURL.protocol = `${protocol}:`;
  }

  if (port === undefined) {
    cloneURL.port = '';
  } else {
    cloneURL.port = port.toString();
  }

  return cloneURL.href;
};

/**
 * The `useUpstream` middleware sents the request to the upstream and captures
 * the response.
 * @param context - The context of the middleware pipeline
 * @param next - The function to invoke the next middleware in the pipeline
 */
export const useUpstream: Middleware = async (
  context,
  next,
) => {
  const { request, upstream } = context;

  if (upstream === null) {
    await next();
    return;
  }

  const url = rewriteURL(
    request.url,
    upstream,
  );
  context.request = new Request(url, context.request);

  if (upstream.onRequest) {
    const onRequest = castToIterable(upstream.onRequest);
    for await (const fn of onRequest) {
      context.request = await fn(context.request, url);
    }
  }

  context.response = (await fetch(context.request)).clone();
  if (upstream.onResponse) {
    const onResponse = castToIterable(upstream.onResponse);
    for await (const fn of onResponse) {
      context.response = await fn(context.response, url);
    }
  }
  await next();
};
