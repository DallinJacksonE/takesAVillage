// Import jest-dom matchers like .toBeInTheDocument()
import "@testing-library/jest-dom";

class MockResizeObserver {
  observe() { }
  unobserve() { }
  disconnect() { }
}

global.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;
if (typeof window !== "undefined") {
  window.ResizeObserver = MockResizeObserver as unknown as typeof ResizeObserver;
}
