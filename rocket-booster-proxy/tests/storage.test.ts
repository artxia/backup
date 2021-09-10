import { WorkersKV } from '../src/storage';

class WorkersKVMock {
  public store: Record<string, string> = {};

  get(key: string): string | null {
    return this.store[key] || null;
  }

  put(key: string, value: string): void {
    this.store[key] = value;
  }

  delete(key: string): void {
    delete this.store[key];
  }
}

beforeAll(() => {
  (globalThis as any).DATABASE = new WorkersKVMock();
});

const storage = new WorkersKV();

test('storage.ts -> putItem()', async () => {
  expect(await storage.put('test-key', 1)).toBeUndefined();
});

test('storage.ts -> get()', async () => {
  expect(await storage.put<Record<string, string>>('test-key', {
    'test-json-key': 'test-value',
  })).toBeUndefined();

  const result = await storage.get<Record<string, string>>('test-key');
  expect(result['test-json-key']).toEqual('test-value');
  expect(await storage.get<Record<string, string>>('non-exist-key')).toBeUndefined();
});

test('storage.ts -> delete()', async () => {
  expect(await storage.put<Record<string, string>>('test-key', {
    'test-json-key': 'test-value',
  })).toBeUndefined();
  expect(await storage.delete('test-key')).toBeUndefined();
  expect(await storage.get<Record<string, string>>('test-key')).toBeUndefined();
});
