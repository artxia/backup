import useReflare from '../../src';

test('upstream -> basic', async () => {
  const request = new Request(
    'https://localhost/get',
  );

  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
  expect(response.url).toBe('https://httpbin.org/get');
});
