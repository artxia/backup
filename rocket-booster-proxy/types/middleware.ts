import { UpstreamOptions } from './middlewares/upstream';

import { Route } from '.';

export interface Context {
  route: Route;
  hostname: string;
  request: Request;
  response: Response;
  upstream: UpstreamOptions | null;
}

export type Middleware = (
  context: Context,
  next: () => Promise<void | null> | void | null,
) => Promise<void | null> | void | null;

export interface Pipeline {
  push: (...middlewares: Middleware[]) => void | null;
  execute: (context: Context) => Promise<void | null>;
}
