import { test, expect } from 'vitest';

import { WorkersKV } from '../../src/database';

declare const TEST_NAMESPACE: string;

interface TestInterface {
  string: string;
  number: number;
}

test('workers-kv.ts -> WorkersKV', async () => {
  const database = new WorkersKV(TEST_NAMESPACE);
  await database.put<TestInterface>('test', {
    string: 'test',
    number: 0,
  });

  const existResult = await database.get<TestInterface>('test');
  expect(existResult).not.toBeNull();
  expect(existResult?.string).toEqual('test');
  expect(existResult?.number).toEqual(0);

  const nullResult = await database.get<TestInterface>('null');
  expect(nullResult).toBeNull();
});
