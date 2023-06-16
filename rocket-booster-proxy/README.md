![Header](https://raw.githubusercontent.com/xiaoyang-sde/reflare/master/.github/img/header.jpg)

<div align="center">

[![GitHub Actions](https://img.shields.io/github/actions/workflow/status/xiaoyang-sde/reflare/node.yml?branch=master&style=for-the-badge&logo=github)](https://github.com/xiaoyang-sde/reflare/actions)
[![Codecov Coverage](https://img.shields.io/codecov/c/github/xiaoyang-sde/reflare?style=for-the-badge&logo=codecov)](https://app.codecov.io/gh/xiaoyang-sde/reflare/)
[![Package Version](https://img.shields.io/npm/v/reflare?style=for-the-badge&logo=npm&color=red)](https://www.npmjs.com/package/reflare)
[![Download Statistics](https://img.shields.io/npm/dt/reflare?style=for-the-badge&logo=npm&color=blue)](https://www.npmjs.com/package/reflare)

[![forthebadge](https://forthebadge.com/images/badges/made-with-typescript.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/ctrl-c-ctrl-v.svg)](https://forthebadge.com)
[![forthebadge](https://forthebadge.com/images/badges/built-with-love.svg)](https://forthebadge.com)

[📦 Releases](https://github.com/xiaoyang-sde/reflare/releases) |
[📔 Examples](#examples) |
[⚙️ Route Definition](#route-definition) |
[☕ Buy Me a Coffee](https://www.buymeacoffee.com/xiaoyang.liu)
</div>

🚀 **Reflare** is a lightweight and scalable reverse proxy and load balancing library built for [Cloudflare Workers](https://workers.cloudflare.com). It sits in front of web servers (e.g. web application, storage platform, or RESTful API), forwards HTTP requests or WebSocket traffics from clients to upstream servers, and transforms responses with several optimizations to improve page loading time.

- ⚡ Serverless: Publish instantly to the auto-scaling serverless platform built by Cloudflare. There's no need to manage virtual machines or containers.
- ✈️ Load Balancing: Distribute incoming traffics among different upstream services.
- ⚙️ Hackable: Deliver unique content based on visitor attributes, conduct A/B testing, or build middlewares to hook into the lifecycle. (Experimental)
- 🛳️ Dynamic Route Definition (Experimental): Store and update route definitions with Workers KV to avoid redundant redeployment.

## Installation

### Start with `reflare-template`

- Generate a new project from [reflare-template](https://github.com/xiaoyang-sde/reflare-template) and install the dependencies.

```console
npm init cloudflare reflare-app https://github.com/xiaoyang-sde/reflare-template
cd reflare-app
npm install
```

- Authenticate `wrangler` with a Cloudflare account.

```console
npx wrangler login
```

- Edit or add route definitions in `src/index.ts`. Please read the examples and the documentation below for more details.

- Run `npm run dev` to preview Reflare with a local development server.

- Run `npm run publish` to publish Reflare on Cloudflare Workers.

### Integrate with existing project

- Install the `reflare` package.

```console
npm install reflare
```

Import `useReflare` from `reflare`. `useReflare` accepts these options:

- `provider`: The location of the list of route definitions. (optional, defaults to `static`)
  - `static`: Reflare loads the route definitions from `routeList`.
  - `kv`: Reflare loads the route definitions from [Workers KV](https://developers.cloudflare.com/workers/learning/how-kv-works). (Experimental)
- `routeList`: The initial list of route definitions. (optional, defaults to `[]`, **ignored if `provider` is not `static`**)
- `namespace`: The Workers KV namespace that stores the list of route definitions. (**required if `provider` is `kv`**)

`useReflare` returns an object with the `handle` method and `push` method.

- The `handle` method takes the inbound [Request](https://developers.cloudflare.com/workers/runtime-apis/request) to the Worker and returns the [Response](https://developers.cloudflare.com/workers/runtime-apis/request) fetched from the upstream service.
- The `push` method takes a route and appends it to `routeList`.

```ts
import useReflare from 'reflare';

export default {
  async fetch(
    request: Request,
  ): Promise<Response> {
    const reflare = await useReflare();

    reflare.push({
      path: '/*',
      upstream: {
        domain: 'httpbin.org',
        protocol: 'https',
      },
    });

    return reflare.handle(request);
  },
};
```

Edit the route definition to change the behavior of Reflare. For example, the route definition below lets Reflare add the `access-control-allow-origin: *` header to each response from the upstream service.

```ts
{
  path: '/*',
  upstream: {
    domain: 'httpbin.org',
    protocol: 'https',
  },
  cors: {
    origin: '*',
  },
}
```

## Examples

### Mirror of MDN Web Docs

Set up a reverse proxy for [MDN Web Docs](https://developer.mozilla.org):

```ts
{
  path: '/*',
  upstream: {
    domain: 'developer.mozilla.org',
    protocol: 'https',
  },
}
```

### WebSocket

Set up a reverse proxy for [wss://echo.websocket.org](wss://echo.websocket.org):

```ts
{
  path: '/*',
  upstream: {
    domain: 'echo.websocket.org',
    protocol: 'https',
  },
}
```

### S3 Bucket

Set up a reverse proxy for [https://example.s3.amazonaws.com](https://example.s3.amazonaws.com) and add custom headers to the response:

```ts
{
  path: '/*',
  upstream: {
    domain: 'example.s3.amazonaws.com',
    protocol: 'https',
  },

  headers: {
    response: {
      'x-response-header': 'Hello from Reflare',
    },
  },

  cors: {
    origin: ['https://www.example.com'],
    methods: ['GET', 'POST'],
    credentials: true,
  },
}
```

## Route Definition

### Route Matching

Reflare implements express-like route matching. Reflare matches the path and HTTP method of each incoming request with the list of route definitions and forwards the request to the first matched route.

- `domain` (`string | string[]`): The domain name or the list of domain names that matches the domain name in the incoming request's URL
- `path` (`string | string[]`): The path or the list of paths that matches the route
- `methods` (`string[]`): The list of HTTP methods that match the route

```ts
// Matches all requests
reflare.push({
  path: '/*',
  /* ... */
});

// Matches all requests that are accessing the Cloudflare Workers instance
// through `template.reflare.workers.dev`
reflare.push({
  domain: 'template.reflare.workers.dev',
  path: '/*',
  /* ... */
});

// Matches GET and POST requests with path `/api`
reflare.push({
  path: '/api',
  methods: ['GET', 'POST'],
});

// Matches GET requests with path ending with `.json` or `.yaml` in `/data`
reflare.push({
  path: ['/data/*.json', '/data/*.yaml'],
  methods: ['GET'],
});
```

### Upstream

- `domain` (`string`): The domain name of the upstream server
- `protocol` (`string`): The protocol scheme of the upstream server (optional, defaults to `'https'`)
- `port` (`number`): The port of the upstream server (optional, defaults to `80` or `443` based on `protocol`)
- `timeout` (`number`): The maximum wait time on a request to the upstream server (optional, defaults to `10000`)
- `weight` (`number`): The weight of the server that will be accounted for as part of the load balancing decision (optional, defaults to `1`)
- `onRequest(request: Request, url: string)`: The callback function that will be called before sending the request to upstream
- `onResponse(response: Response, url: string)`: The callback function that will be called after receiving the response from upstream

```ts
reflare.push({
  path: '/*',
  upstream: {
    domain: 'httpbin.org',
    protocol: 'https',
    port: 443,
    timeout: 10000,
    weight: 1,
  },
  /* ... */
});
```

The `onRequest` and `onResponse` fields accept callback functions that could change the content of the request or response. For example, the following example replaces the URL of the request and sets the `cache-control` header of the response based on its URL. These fields accept either a standalone function or a list of functions. The function could be either `async` or non-`async`.

```ts
reflare.push({
  path: '/*',
  upstream: {
    domain: 'httpbin.org',
    protocol: 'https',
    port: 443,
    timeout: 10000,
    weight: 1,

    onRequest: (request: Request, url: string): Request => {
      // Modifies the URL of the request
      return new Request(url.replace('/original/request/path', ''), request);
    },

    onResponse: (response: Response, url: string): Response => {
      // If the URL ends with `.html` or `/`, sets the `cache-control` header
      if (url.endsWith('.html') || url.endsWith('/')) {
        response.headers.set('cache-control', 'public, max-age=240, s-maxage=60');
      }
      return response;
    }
  },
  /* ... */
});
```

### Load Balancing

To load balance HTTP traffic to a group of servers, pass an array of server configurations to `upstream`. The load balancer will forward the request to an upstream server based on the `loadBalancing.policy` option.

- `random`: The load balancer will select a random upstream server from the server group. The optional `weight` parameter in the server configuration could influence the load balancing algorithm.
- `ip-hash`: The client's IP address is used as a hashing key to select the upstream server from the server group. It ensures that the requests from the same client will always be directed to the same server.

```ts
reflare.push({
  path: '/*',
  loadBalancing: {
    policy: 'random',
  },
  upstream: [
    {
      domain: 's1.example.com',
      protocol: 'https',
      weight: 20,
    },
    {
      domain: 's2.example.com',
      protocol: 'https',
      weight: 30,
    },
    {
      domain: 's3.example.com',
      protocol: 'https',
      weight: 50,
    },
  ],
  /* ... */
});
```

### Firewall

Each incoming request is inspected against the firewall rules defined in the `firewall` property of the options object. The request will be blocked if it matches at least one firewall rule.

- `field`: The property of the incoming request to be inspected
  - `asn`: The ASN number of the incoming request (`number`)
  - `ip`: The IP address of the incoming request, e.g. `1.1.1.1` (`string`)
  - `hostname`: The content of the `host` header, e.g. `github.com` (`string | undefined`)
  - `user-agent`: The content of the `user-agent` header, e.g. `Mozilla/5.0` (`string | undefined`)
  - `country`: The two-letter country code in the request, e.g. `US` (`string | undefined`)
  - `continent`: The continent of the incoming request, e.g. `NA` (`string | undefined`)
- `value` (`string | string[] | number | number[] | RegExp`): The value of the firewall rule
- `operator`: The operator to be used to determine if the request is blocked
  - `equal`: Block the request if `field` is equal to `value`
  - `not equal`: Block the request if `field` is not equal to `value`
  - `match`: Block the request if `value` matches `field` (Expect `field` to be `string` and `value` to be `RegExp`)
  - `not match`: Block the request if `value` doesn't match `field` (Expect `field` to be `string` and `value` to be `RegExp`)
  - `in`: Block the request if `field` is in `value` (Expect `value` to be `Array`)
  - `not in`: Block the request if `field` is not in `value` (Expect `value` to be `Array`)
  - `contain`: Block the request if `field` contains `value` (Expect `field` and `value` to be `string`)
  - `not contain`: Block the request if `field` doesn't contain `value` (Expect `field` and `value` to be `string`)
  - `greater`: Block the request if `field` is greater than `value` (Expect `field` and `value` to be `number`)
  - `less`: Block the request if `field` is less than `value` (Expect `field` and `value` to be `number`)

```ts
reflare.push('/', {
  path: '/*',
  /* ... */
  firewall: [
    {
      field: 'ip',
      operator: 'in',
      value: ['1.1.1.1', '1.0.0.1'],
    },
    {
      field: 'user-agent',
      operator: 'match',
      value: /Chrome/,
    }
  ],
});
```

### Headers

- `request` (`Record<string, string>`): Sets request header going upstream to the backend. Accepts an object. (optional, defaults to `{}`)
- `response` (`Record<string, string>`): Sets response header coming downstream to the client. Accepts an object. (optional, defaults to `{}`)

```ts
reflare.push({
  path: '/*',
  /* ... */
  headers: {
    request: {
      'x-example-header': 'hello server',
    },
    response: {
      'x-example-header': 'hello client',
    },
  },
});
```

### Cross-Origin Resource Sharing (CORS)

- `origin`: Configures the `Access-Control-Allow-Origin` CORS header. (optional, defaults to `false`)
  - `boolean`: set to `true` to reflect the origin of the request, or set to `false` to disable CORS.
  - `string[]`: an array of acceptable origins.
  - `*`: allow any origin to access the resource.

- `methods` (`string[]`): Configures the `Access-Control-Allow-Methods` CORS header. Expect an array of valid HTTP methods or `*`. (optional, defaults to reflecting the method specified in the request’s `Access-Control-Request-Method` header)

- `allowedHeaders` (`string[]`): Configures the `Access-Control-Allow-Headers` CORS header. Expect an array of HTTP headers or *. (optional, defaults to reflecting the headers specified in the request’s `Access-Control-Request-Headers` header.)

- `exposedHeaders` (`string[]`): Configures the `Access-Control-Expose-Headers` CORS header. Expect an array of HTTP headers or `*`. (optional, defaults to `[]`)

- `credentials` (`boolean`): Configures the `Access-Control-Allow-Credentials` CORS header. Set to true to pass the header, or it is omitted. (optional, defaults to `false`)

- `maxAge` (`number`): Configures the `Access-Control-Max-Age` CORS header. Set to an integer to pass the header, or it is omitted. (optional)

```ts
reflare.push({
  path: '/*',
  /* ... */
  cors: {
    origin: true,
    methods: [
      'GET',
      'POST',
    ],
    allowedHeaders: [
      'Example-Header',
    ],
    exposedHeaders: [
      'Example-Header',
    ],
    credentials: true,
    maxAge: 86400,
  },
});
```

## 🛳️ Dynamic Route Definition (Experimental)

Reflare could load the route definitions from Workers KV. Set the `provider` to `kv` and `namespace` to a Workers KV namespace (e.g. `REFLARE`) that binds to the current Worker. Reflare fetches the route definitions from `namespace` and handles each incoming request with the latest route definitions.

```ts
import useReflare from 'reflare';

declare const REFLARE: KVNamespace;

export default {
  async fetch(
    request: Request,
  ): Promise<Response> {
    const reflare = await useReflare({
      provider: 'kv',
      namespace: REFLARE,
    });

    return reflare.handle(request);
  },
};
```

The route definitions should be stored as a JSON array in the `route-list` key of `namespace`. The KV namespace could be modified with [`wrangler`](https://developers.cloudflare.com/workers/cli-wrangler/commands#kvkey) or [Cloudflare API](https://api.cloudflare.com/#workers-kv-namespace-write-key-value-pair).

```console
wrangler kv:key put --binding=[namespace] 'route-list' '[{"path":"/*","upstream":{"domain":"httpbin.org","protocol":"https"}}]'
```

## Contributors

[![Contributors](https://contrib.rocks/image?repo=xiaoyang-sde/reflare)](https://github.com/xiaoyang-sde/reflare/graphs/contributors)
