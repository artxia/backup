import { Database } from '../../types/database';

/**
 * The interface for CRUD operations on Workers KV.
 */
export class WorkersKV implements Database {
  namespace: KVNamespace;

  constructor(
    namespace: KVNamespace,
  ) {
    this.namespace = namespace;
  }

  get = async <Type>(key: string): Promise<Type | null> => {
    const value = await this.namespace.get<Type>(key, {
      type: 'json',
      cacheTtl: 60,
    });
    return value;
  };

  put = async <Type>(key: string, value: Type): Promise<void> => {
    await this.namespace.put(key, JSON.stringify(value));
  };

  delete = async (key: string): Promise<void> => {
    await this.namespace.delete(key);
  };
}
