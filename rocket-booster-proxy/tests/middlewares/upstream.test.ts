import { test, expect } from 'vitest';

import useReflare from '../../src';

test('upstream.ts -> upstream', async () => {
  const request = new Request('https://localhost/get');

  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbingo.org/get');
});

test('upstream.ts -> onRequest', async () => {
  const request = new Request('https://localhost/foo/bar');
  const reflare = await useReflare();

  reflare.push({
    path: '/foo*',
    upstream: {
      domain: 'httpbingo.org',
      onRequest: [
        (_, url) => new Request(url.replace('foo/bar', 'get')),
      ],
    },
  });

  const response = await reflare.handle(request);

  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbingo.org/get');
});

test('upstream.ts -> onResponse', async () => {
  const request = new Request('https://localhost/foo/bar/baz');
  const reflare = await useReflare();

  reflare.push({
    path: '/foo*',
    upstream: {
      domain: 'httpbingo.org',
      onResponse: [
        (response) => {
          response.headers.set('x-response-header', 'test');
          return response;
        },
        async (response) => {
          response.headers.set('content-length', '0');
          return response;
        },
      ],
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.get('x-response-header')).toEqual('test');
  expect(response.headers.get('content-length')).toEqual('0');
});

test('upstream.ts -> multiple paths', async () => {
  const request = new Request('https://localhost/get');

  const reflare = await useReflare();
  reflare.push({
    path: ['/foo', '/bar', '/get'],
    upstream: { domain: 'httpbingo.org' },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbingo.org/get');
});

test('upstream.ts -> domain', async () => {
  const reflare = await useReflare();
  reflare.push({
    domain: 'example.com',
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
  });

  {
    const request = new Request('https://example.com/get');
    const response = await reflare.handle(request);
    expect(response.status).toBe(200);
    expect(response.url).toBe('https://httpbingo.org/get');
  }

  {
    const request = new Request('https://test.com/get');
    const response = await reflare.handle(request);
    expect(response.status).toBe(500);
  }
});
