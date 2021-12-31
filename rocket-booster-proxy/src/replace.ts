import { Middleware } from '../types/middleware';
import { ReplaceEntry } from '../types/replace';

export const useReplace: Middleware = async (
  context,
  next,
) => {
  const { request, response, options } = context;
  if (options.replace === undefined) {
    await next();
    return;
  }

  const path = new URL(request.url).pathname;
  const matchedEntries: ReplaceEntry[] = [];
  for (const patch of options.replace) {
    if (
      patch.entries.length > 0
      && (patch.path === undefined || patch.path.test(path))
    ) {
      patch.entries.forEach((entry) => {
        matchedEntries.push(entry);
      });
    }
  }

  const responseContent = await response.text();
  const replacedContent = matchedEntries.reduce(
    (prevContent, { from, to }) => prevContent.replaceAll(from, to),
    responseContent,
  );
  context.response = new Response(replacedContent, response);

  await next();
};
