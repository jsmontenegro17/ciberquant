import { useSyncExternalStore } from "react";
let selected = "";
const listeners = new Set<() => void>();
export function useAccountSelection() {
  const value = useSyncExternalStore(
    (callback) => {
      listeners.add(callback);
      return () => {
        listeners.delete(callback);
      };
    },
    () => selected,
  );
  return [
    value,
    (id: string) => {
      selected = id;
      listeners.forEach((listener) => listener());
    },
  ] as const;
}
