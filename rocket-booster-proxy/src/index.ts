import { useFirewall } from './firewall';
import { useRequestHeaders, useResponseHeaders } from './headers';
import { useSelectUpstream } from './load-balancing';
import { useWebSocket } from './websocket';
import { useUpstream } from './upstream';
import { useCustomError } from './custom-error';
import { useCORS } from './cors';

import { getHostname } from './utils';
import { usePipeline } from './middleware';

import { Proxy, Configuration } from '../types/index';
import { Context } from '../types/middleware';

export default function useProxy(
  options: Configuration,
): Proxy {
  const pipeline = usePipeline(
    useFirewall,
    useRequestHeaders,
    useSelectUpstream,
    useUpstream,
    useWebSocket,
    useCustomError,
    useCORS,
    useResponseHeaders,
  );

  const apply = async (request: Request): Promise<Response> => {
    const context: Context = {
      options,
      request,
      hostname: getHostname(request),
      response: new Response('Unhandled response'),
      upstream: null,
    };

    await pipeline.execute(context);
    return context.response;
  };

  return {
    apply,
  };
}
