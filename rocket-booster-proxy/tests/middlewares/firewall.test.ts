import useReflare from '../../src';

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

test('firewall.ts -> country pass', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    firewall: [
      {
        field: 'country',
        operator: 'in',
        value: ['CN', 'KP', 'SY', 'PK'],
      },
    ],
  });

  const response = await reflare.handle(request);
  expect(response.status).toBe(200);
});

test('firewall.ts -> ip block with in', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    firewall: [
      {
        field: 'ip',
        operator: 'in',
        value: ['1.1.1.1', '1.0.0.1'],
      },
    ],
  });

  const response = await reflare.handle(request);
  expect(response.status).not.toBe(200);
});

test('firewall.ts -> ip block with match', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    firewall: [
      {
        field: 'ip',
        operator: 'match',
        value: '1.1.1.*',
      },
    ],
  });

  const response = await reflare.handle(request);
  expect(response.status).not.toBe(200);
});

test('firewall.ts -> ip block with contain', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    firewall: [
      {
        field: 'ip',
        operator: 'contain',
        value: '1',
      },
    ],
  });

  const response = await reflare.handle(request);
  expect(response.status).not.toBe(200);
});

test('firewall.ts -> user-agent block with not contain', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    firewall: [
      {
        field: 'user-agent',
        operator: 'not contain',
        value: '1234567',
      },
    ],
  });

  const response = await reflare.handle(request);
  expect(response.status).not.toBe(200);
});

test('firewall.ts -> invalid operator', async () => {
  const reflare = await useReflare();
  reflare.push({
    path: '/*',
    upstream: { domain: 'httpbin.org' },
    firewall: [
      {
        field: 'ip',
        operator: 'greater',
        value: '1.1.1.1',
      },
    ],
  });

  const response = await reflare.handle(request);
  expect(response.status).not.toBe(200);
});
