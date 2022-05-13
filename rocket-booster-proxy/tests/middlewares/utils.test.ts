import {
  isSameOrigin,
  createResponse,
  getHostname,
} from '../../src/utils';
import { UpstreamOptions } from '../../types/middlewares/upstream';

test('utils.ts -> isSameOrigin()', () => {
  const upstream: UpstreamOptions = {
    domain: 'httpbin.org',
    protocol: 'https',
  };
  const truthyUrl = new URL('https://httpbin.org/test');
  const falsyUrl = new URL('https://github.com/test');
  expect(isSameOrigin(truthyUrl, upstream)).toEqual(true);
  expect(isSameOrigin(falsyUrl, upstream)).toEqual(false);
});

test('utils.ts -> createResponse()', async () => {
  const response = createResponse(
    'Test response body',
    403,
  );
  expect(response.status).toEqual(403);
  expect(response.ok).toEqual(false);
  await expect(response.text()).resolves.toEqual('Test response body');
});

test('utils.ts -> getHostname()', () => {
  const url = 'https://developer.mozilla.org:443/en-US/docs/';
  const request = new Request(url);
  const hostname = getHostname(request);
  expect(hostname).toEqual('developer.mozilla.org');
});
