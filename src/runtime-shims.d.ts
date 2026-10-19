declare module 'react' {
  export type RefObject<T = unknown> = { current: T };
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: any[]): T;
  export function useEffect(callback: () => void | (() => void), deps?: any[]): void;
  export function useMemo<T>(callback: () => T, deps: any[]): T;
  export function useRef<T>(initial: T | null): { current: T | null };
  export function useState<T>(initial: T): [T, (value: T | ((previous: T) => T)) => void];
  const React: any;
  export default React;
}

declare module 'react-dom/client' {
  export const createRoot: any;
}

declare module 'react/jsx-runtime' {
  export const Fragment: any;
  export const jsx: any;
  export const jsxs: any;
}

declare module '*.css';

declare namespace JSX {
  interface IntrinsicElements { [element: string]: any; }
}
