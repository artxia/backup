import { test, expect } from 'vitest';

import useReflare from '../../src';
import { UpstreamOptions } from '../../types/middlewares';

const upstream: UpstreamOptions[] = [
  {
    domain: 'javascript.info',
    protocol: 'https',
    weight: 0,
  },
  {
    domain: 'httpbingo.org',
    protocol: 'https',
    weight: 1,
  },
  {
    domain: 'google.com',
    protocol: 'https',
    weight: 0,
  },
];

const request = new Request(
  'https://localhost/get',
  {
    headers: new Headers({
      host: 'github.com',
      'cf-connecting-ip': '1.1.1.1',
      'user-agent': 'Mozilla/5.0',
    }),
    method: 'GET',
  },
);

test('load-balancing.ts -> ip-hash', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream,
    loadBalancing: {
      policy: 'ip-hash',
    },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbingo.org/get');
});

test('load-balancing.ts -> weighted random', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream,
    loadBalancing: {
      policy: 'random',
    },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbingo.org/get');
});
