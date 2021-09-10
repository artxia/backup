import { Storage } from '../types/storage';

declare const DATABASE: KVNamespace;

export class WorkersKV implements Storage {
  get = async <Type>(key: string): Promise<Type | void> => {
    const value = await DATABASE.get(key);
    if (typeof value === 'string') {
      return JSON.parse(value);
    }
    return undefined;
  }

  put = async <Type>(key: string, value: Type): Promise<void> => {
    await DATABASE.put(key, JSON.stringify(value));
  }

  delete = async (key: string): Promise<void> => {
    await DATABASE.delete(key);
  }
}
