export interface Storage {
  get<Type>(key: string): Promise<Type | void>
  put<Type>(key: string, value: Type): Promise<void>
  delete(key: string): Promise<void>
}
