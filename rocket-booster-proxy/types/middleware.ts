import { Options } from './proxy';
import { UpstreamOptions } from './upstream';
import { Storage } from './storage';

export interface Context {
  hostname: string;
  request: Request;
  response: Response;
  options: Options;
  storage: Storage;
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
