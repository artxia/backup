import { Middleware } from '../../types/middleware';
import { UpstreamOptions } from '../../types/middlewares/upstream';
import { LoadBalancingHandler, LoadBalancingPolicy } from '../../types/middlewares/load-balancing';

const validateUpstream = (
  upstream: UpstreamOptions,
): void => {
  if (upstream.domain === undefined) {
    throw new Error('Invalid \'upstream\' field in the option object');
  }
};

export const ipHashHandler: LoadBalancingHandler = (
  upstream,
  request,
) => {
  const ipString = request.headers.get('cf-connecting-ip') || '0.0.0.0';
  const userIP = ipString.split('.').map(
    (octect, index, array) => parseInt(octect, 10) * (256 ** (array.length - index - 1)),
  ).reduce(
    (accumulator, current) => accumulator + current,
  );
  return upstream[userIP % upstream.length];
};

export const randomHandler: LoadBalancingHandler = (
  upstream,
) => {
  const weights = upstream.map(
    (option) => (option.weight === undefined ? 1 : option.weight),
  );
  const totalWeight = weights.reduce(
    (acc, num, index) => {
      const sum = acc + num;
      weights[index] = sum;
      return sum;
    },
  );
  if (totalWeight === 0) {
    throw new Error('Total weights should be greater than 0.');
  }
  const random = Math.random() * totalWeight;
  for (const index of weights.keys()) {
    if (weights[index] >= random) {
      return upstream[index];
    }
  }
  return upstream[Math.floor(Math.random() * upstream.length)];
};

const handlersMap: Record<LoadBalancingPolicy, LoadBalancingHandler> = {
  random: randomHandler,
  'ip-hash': ipHashHandler,
};

/**
 * The `useLoadBalancing` middleware picks an upstream server based on the load
 * balancing policy.
 * @param context - The context of the middleware pipeline
 * @param next - The function to invoke the next middleware in the pipeline
 */
export const useLoadBalancing: Middleware = async (
  context,
  next,
) => {
  const { request, route } = context;
  const { upstream, loadBalancing } = route;

  if (upstream === undefined) {
    throw new Error('The required \'upstream\' field in the option object is missing');
  } else if (Array.isArray(upstream)) {
    upstream.forEach(validateUpstream);
  } else {
    validateUpstream(upstream);
  }

  const upstreamArray = Array.isArray(upstream) ? upstream : [upstream];
  if (loadBalancing === undefined) {
    context.upstream = randomHandler(upstreamArray, request);
    await next();
    return;
  }

  const policy = loadBalancing.policy || 'random';
  const policyHandler = handlersMap[policy];
  context.upstream = policyHandler(upstreamArray, request);
  await next();
};
