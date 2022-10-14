import { Middleware } from '../../types/middleware';
import { UpstreamOptions, onResponseCallback, onRequestCallback } from '../../types/middlewares/upstream';
import { convertToArray } from '../utils';

export const cloneRequest = (
  url: string,
  request: Request,
): Request => {
  const requestInit: CfRequestInit = {
    body: request.body,
    method: request.method,
    headers: request.headers,
  };
  return new Request(url, requestInit);
};

export const getURL = (
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

  const url = getURL(
    request.url,
    upstream,
  );

  const onRequest = upstream.onRequest
    ? convertToArray<onRequestCallback>(upstream.onRequest)
    : null;

  const onResponse = upstream.onResponse
    ? convertToArray<onResponseCallback>(upstream.onResponse)
    : null;

  let upstreamRequest = cloneRequest(url, request);

  if (onRequest) {
    upstreamRequest = onRequest.reduce(
      (prevRequest: Request, fn: onRequestCallback) => fn(cloneRequest(url, prevRequest), url),
      upstreamRequest,
    );
  }

  context.response = await fetch(upstreamRequest);

  if (onResponse) {
    context.response = onResponse.reduce(
      (prevResponse: Response, fn: onResponseCallback) => fn(new Response(prevResponse.body, prevResponse), url),
      new Response(context.response.body, context.response),
    );
  }

  await next();
};
