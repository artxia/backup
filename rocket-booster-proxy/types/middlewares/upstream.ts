export interface UpstreamOptions {
  domain: string;
  protocol?: 'http' | 'https';
  port?: number;
  timeout?: number;
  weight?: number;
  onRequest?: (request: Request, url: string) => Request;
  onResponse?: (response: Response, url: string) => Response;
}
