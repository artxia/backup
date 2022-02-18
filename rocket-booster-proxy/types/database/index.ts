export interface Database {
  get<Type>(key: string): Promise<Type | null>
  put<Type>(key: string, value: Type): Promise<void>
  delete(key: string): Promise<void>
}
