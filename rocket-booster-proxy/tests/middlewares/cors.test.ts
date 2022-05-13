import useReflare from '../../src';

interface HTTPBinGetResponse {
  headers: Record<string, string>;
  origin: string;
}

const request = new Request(
  'https://httpbin.org/get',
  {
    headers: new Headers({
      origin: 'https://httpbin.org',
      'Access-Control-Request-Method': 'GET',
    }),
    method: 'GET',
  },
);

test('CORS -> methods', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    cors: {
      origin: ['https://httpbin.org'],
      methods: ['GET', 'POST'],
    },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  const responseObject = await response.json<HTTPBinGetResponse>();
  expect(responseObject.headers.Origin).toBe('https://httpbin.org');
  expect(response.headers.get('Access-Control-Allow-Methods')).toBe('GET,POST');
});

test('CORS -> Max Age', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    cors: {
      origin: true,
      maxAge: 3600,
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.get('access-control-max-age')).toBe('3600');
});

test('CORS -> Access-Control-Allow-Credentials', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    cors: {
      origin: true,
      credentials: true,
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.has('Access-Control-Allow-Credentials')).toBeTruthy();
});

test('CORS -> Access-Control-Allow-Origin', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    cors: {
      origin: true,
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.has('Access-Control-Allow-Origin')).toBeTruthy();
});

test('CORS -> Access-Control-Allow-Origin wildcard', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    cors: {
      origin: '*',
    },
  });

  const response = await reflare.handle(request);
  expect(response.headers.get('Access-Control-Allow-Origin')).toBe('*');
});
