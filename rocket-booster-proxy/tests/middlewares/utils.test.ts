import { test, expect } from 'vitest';

import {
  isSameOrigin,
  getHostname,
} from '../../src/utils';
import { UpstreamOptions } from '../../types/middlewares/upstream';

test('utils.ts -> isSameOrigin()', () => {
  const upstream: UpstreamOptions = {
    domain: 'httpbingo.org',
    protocol: 'https',
  };
  const truthyUrl = new URL('https://httpbingo.org/test');
  const falsyUrl = new URL('https://github.com/test');
  expect(isSameOrigin(truthyUrl, upstream)).toEqual(true);
  expect(isSameOrigin(falsyUrl, upstream)).toEqual(false);
});

test('utils.ts -> getHostname()', () => {
  const url = 'https://developer.mozilla.org:443/en-US/docs/';
  const request = new Request(url);
  const hostname = getHostname(request);
  expect(hostname).toEqual('developer.mozilla.org');
});
