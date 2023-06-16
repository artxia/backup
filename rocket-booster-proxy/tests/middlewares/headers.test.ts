import { test, expect } from 'vitest';

import useReflare from '../../src';

interface HTTPBinGetResponse {
  headers: Record<string, string>;
  origin: string;
}

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

test('headers.ts -> set request headers', async () => {
  const reflare = await useReflare();

  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    headers: {
      request: {
        accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'cache-control': 'max-age=100',
      },
      response: {
        'x-response-header': 'Hello from reflare',
      },
    },
  });

  const response = await reflare.handle(request);
  const requestInfo = await response.json() as HTTPBinGetResponse;
  expect(requestInfo.headers['Accept-Encoding']).toMatch('gzip, deflate, br');
  expect(requestInfo.headers.Accept)
    .toMatch('text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8');
  expect(requestInfo.headers['Cache-Control']).toMatch('max-age=100');
});

test('headers.ts -> set response headers', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    headers: {
      request: {
        accept: 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'accept-encoding': 'gzip, deflate, br',
        'cache-control': 'max-age=100',
      },
      response: {
        'x-response-header': 'Hello from reflare',
        connection: 'keep-alive',
        'content-type': 'application/json',
      },
    },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.headers.get('x-response-header')).toMatch('Hello from reflare');
  expect(response.headers.get('connection')).toMatch('keep-alive');
  expect(response.headers.get('content-type')).toMatch('application/json');
});

test('headers.ts -> delete request headers', async () => {
  const reflare = await useReflare();

  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    headers: {
      request: {
        'user-agent': '',
        'test-header': '',
      },
    },
  });

  const response = await reflare.handle(request);
  const requestInfo = await response.json() as HTTPBinGetResponse;
  expect(requestInfo.headers['user-agent']).toBeUndefined();
  expect(requestInfo.headers['test-header']).toBeUndefined();
});

test('headers.ts -> delete response headers', async () => {
  const reflare = await useReflare();

  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbingo.org' },
    headers: {
      response: {
        server: '',
        'content-type': '',
        'test-header': '',
      },
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.has('server')).toBeFalsy();
  expect(response.headers.has('content-type')).toBeFalsy();
  expect(response.headers.has('test-header')).toBeFalsy();
});
