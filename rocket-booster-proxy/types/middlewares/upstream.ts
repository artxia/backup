export type RequestCallback = ((request: Request, url: string) => Request)
| ((request: Request, url: string) => Promise<Request>);
export type ResponseCallback = ((response: Response, url: string) => Response)
| ((response: Response, url: string) => Promise<Response>);

export interface UpstreamOptions {
  domain: string;
  protocol?: 'http' | 'https';
  port?: number;
  timeout?: number;
  weight?: number;
  onRequest?: RequestCallback | RequestCallback[];
  onResponse?: ResponseCallback | ResponseCallback[];
}
