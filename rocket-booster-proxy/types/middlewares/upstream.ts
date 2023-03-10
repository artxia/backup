export type RequestCallback = (request: Request, url: string) => Request;
export type ResponseCallback = (response: Response, url: string) => Response;

export interface UpstreamOptions {
  domain: string;
  protocol?: 'http' | 'https';
  port?: number;
  timeout?: number;
  weight?: number;
  onRequest?: RequestCallback | RequestCallback[];
  onResponse?: ResponseCallback | ResponseCallback[];
}
