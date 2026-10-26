import '@testing-library/jest-dom';
import { vi } from 'vitest';

// Polyfill ResizeObserver for Recharts in jsdom
global.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};

// Mock window.URL.createObjectURL for CSV export tests
window.URL.createObjectURL = vi.fn(() => 'blob:mock-url');
window.URL.revokeObjectURL = vi.fn();
