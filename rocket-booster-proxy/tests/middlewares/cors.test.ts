import { test, expect } from 'vitest';

import useReflare from '../../src';

interface HTTPBinGetResponse {
  headers: Record<string, string>;
  origin: string;
}

const request = new Request(
  'https://httpbingo.org/get',
  {
    headers: new Headers({
      origin: 'https://httpbingo.org',
      'Access-Control-Request-Method': 'GET',
    }),
    method: 'GET',
  },
);

test('cors.ts -> \'access-control-allow-methods\'', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    cors: {
      origin: ['https://httpbingo.org'],
      methods: ['GET', 'POST'],
    },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  const responseObject = await response.json() as HTTPBinGetResponse;
  expect(responseObject.headers.Origin).toContain('https://httpbingo.org');
  expect(response.headers.get('access-control-allow-methods')).toBe('GET,POST');
});

test('cors.ts -> \'access-control-max-age\'', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    cors: {
      origin: true,
      maxAge: 3600,
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.get('access-control-max-age')).toBe('3600');
});

test('cors.ts -> \'access-control-allow-credentials\'', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    cors: {
      origin: true,
      credentials: true,
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.has('access-control-allow-credentials')).toBeTruthy();
});

test('cors.ts -> \'access-control-allow-origin\'', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    cors: {
      origin: true,
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.has('access-control-allow-origin')).toBeTruthy();
});

test('cors.ts -> \'access-control-allow-origin\'', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    cors: {
      origin: '*',
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.get('access-control-allow-origin')).toBe('*');
});
