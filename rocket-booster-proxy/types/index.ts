import {
  CORSOptions,
  FirewallOptions,
  HeadersOptions,
  LoadBalancingOptions,
  UpstreamOptions,
} from './middlewares';

export interface Route {
  domain?: string | string[];
  path: string | string[];
  upstream: UpstreamOptions | UpstreamOptions[];
  firewall?: FirewallOptions[];
  cors?: CORSOptions;
  headers?: HeadersOptions;
  methods?: string[],
  loadBalancing?: LoadBalancingOptions,
}

export type RouteList = Route[];

export interface Reflare {
  handle: (
    request: Request,
  ) => Promise<Response>;
  unshift: (
    route: Route,
  ) => void;
  push: (
    route: Route,
  ) => void;
}

interface StaticOptions {
  provider: 'static',
  routeList: RouteList,
}

interface KVOptions {
  provider: 'kv',
  namespace: KVNamespace,
}

export type Options = StaticOptions | KVOptions;
