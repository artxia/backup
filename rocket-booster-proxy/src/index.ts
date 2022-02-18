import {
  useCORS,
  useFirewall,
  useHeaders,
  useLoadBalancing,
  useUpstream,
} from './middlewares';
import { WorkersKV } from './database';
import { usePipeline } from './middleware';
import { createResponse, getHostname } from './utils';

import {
  Reflare,
  Route,
  RouteList,
  Options,
} from '../types';
import { Context } from '../types/middleware';

const filter = (
  request: Request,
  routeList: RouteList,
): Route | void => {
  const url = new URL(request.url);
  for (const route of routeList) {
    if (
      route.methods === undefined
      || route.methods.includes(request.method)
    ) {
      const re = RegExp(
        `^${
          route.path
            .replace(/(\/?)\*/g, '($1.*)?')
            .replace(/\/$/, '')
            .replace(/:(\w+)(\?)?(\.)?/g, '$2(?<$1>[^/]+)$2$3')
            .replace(/\.(?=[\w(])/, '\\.')
            .replace(/\)\.\?\(([^[]+)\[\^/g, '?)\\.?($1(?<=\\.)[^\\.')
        }/*$`,
      );
      if (url.pathname.match(re)) {
        return route;
      }
    }
  }
  return undefined;
};

const defaultOptions: Options = {
  provider: 'static',
  routeList: [],
};

const useReflare = async (
  options: Options = defaultOptions,
): Promise<Reflare> => {
  const pipeline = usePipeline(
    useFirewall,
    useLoadBalancing,
    useHeaders,
    useCORS,
    useUpstream,
  );

  const routeList: RouteList = [];

  if (options.provider === 'static') {
    for (const route of options.routeList) {
      routeList.push(route);
    }
  }

  if (options.provider === 'kv') {
    const database = new WorkersKV(options.namespace);
    const routeListKV = await database.get<RouteList>('route-list') || [];
    for (const routeKV of routeListKV) {
      routeList.push(routeKV);
    }
  }

  const handle = async (
    request: Request,
  ): Promise<Response> => {
    const route = filter(request, routeList);
    if (route === undefined) {
      return createResponse('Failed to find a route that matches the path and method of the current request', 500);
    }

    const context: Context = {
      request,
      route,
      hostname: getHostname(request),
      response: new Response('Unhandled response'),
      upstream: null,
    };

    try {
      await pipeline.execute(context);
    } catch (error) {
      if (error instanceof Error) {
        context.response = createResponse(error.message, 500);
      }
    }
    return context.response;
  };

  const unshift = (
    route: Route,
  ) => {
    routeList.unshift(route);
  };

  const push = (
    route: Route,
  ) => {
    routeList.push(route);
  };

  return {
    handle,
    unshift,
    push,
  };
};

export default useReflare;
