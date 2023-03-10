import useReflare from '../../src';

test('upstream -> basic', async () => {
  const request = new Request('https://localhost/get');

  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbin.org/get');
});

test('upstream -> onRequest', async () => {
  const request = new Request('https://localhost/foo/bar/baz');
  const reflare = await useReflare();

  reflare.push({
    path: '/foo*',
    upstream: {
      domain: 'httpbin.org',
      onRequest: (_req, url) => {
        const next: string = url.replace('foo/bar/baz', 'get');
        return new Request(next);
      },
    },
  });

  const response = await reflare.handle(request);

  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbin.org/get');
});

test('upstream -> onResponse', async () => {
  const request = new Request('https://localhost/foo/bar/baz');
  const reflare = await useReflare();

  reflare.push({
    path: '/foo*',
    upstream: {
      domain: 'httpbin.org',
      onResponse: [
        (res: Response): Response => {
          const result = 1 + 1;
          res.headers.set('x-foo', result.toString());
          return res;
        },
        (res: Response): Response => {
          res.headers.set('x-bar', 'foo');
          return res;
        },
      ],
    },
  });

  const response = await reflare.handle(request);

  expect(response.headers.get('x-foo')).toEqual('2');
  expect(response.headers.get('x-bar')).toEqual('foo');
});

test('upstream -> with collection of paths', async () => {
  const request = new Request('https://localhost/get');

  const reflare = await useReflare();
  reflare.push({
    path: ['/foo', '/bar', '/get'],
    upstream: { domain: 'httpbin.org' },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbin.org/get');
});
