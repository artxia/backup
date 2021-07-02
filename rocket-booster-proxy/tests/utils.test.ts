import {
  isMobile,
  createResponse,
  getHostname,
} from '../src/utils';

test('utils.ts -> createResponse()', () => {
  const response = createResponse(
    'Test response body',
    403,
  );
  expect(response.status).toEqual(403);
  expect(response.ok).toEqual(false);
  expect(response.body).toEqual('Test response body');
});

test('utils.ts -> isMobile()', () => {
  const userAgents: [string, boolean][] = [
    [
      // Pixel 3, Chrome 90
      `
      Mozilla/5.0 (Linux; Android 11; Pixel 3)
      AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.210 Mobile Safari/537.36
      `,
      true,
    ],
    [
      // Macbook Pro, Chrome 90
      `
      Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)
      AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36
      `,
      false,
    ],
    [
      // Google Crawler
      `
      Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)
      `,
      false,
    ],
  ];

  userAgents.forEach(([userAgent, result]) => {
    expect(isMobile(userAgent)).toEqual(result);
  });
});

test('utils.ts -> getHostname()', () => {
  const url = 'https://developer.mozilla.org:443/en-US/docs/';
  const request = new Request(url);
  const hostname = getHostname(request);
  expect(hostname).toEqual('developer.mozilla.org');
});
