import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { PersistStorage } from 'zustand/middleware';

type ThemeMode = 'light' | 'dark';

interface ThemeState {
  mode: ThemeMode;
  toggle: () => void;
  setMode: (m: ThemeMode) => void;
}

const storage: PersistStorage<ThemeState> = {
  getItem: (name) => {
    const item = localStorage.getItem(name);
    if (!item) return null;
    return JSON.parse(item);
  },
  setItem: (name, value) => {
    localStorage.setItem(name, JSON.stringify(value));
  },
  removeItem: (name) => {
    localStorage.removeItem(name);
  },
};

export const useThemeStore = create<ThemeState>()(
  persist(
    (set, get) => ({
      mode: 'dark',
      toggle: () => set({ mode: get().mode === 'dark' ? 'light' : 'dark' }),
      setMode: (m: ThemeMode) => set({ mode: m }),
    }),
    {
      name: 'theme-storage',
      storage,
    }
  )
);

export default useThemeStore;
