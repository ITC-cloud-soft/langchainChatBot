import { renderHook, act } from '@testing-library/react';
import { useScroll } from '@/hooks/useScroll';

// Mock useResponsive hook since it depends on Material-UI's useMediaQuery
vi.mock('@/hooks/useResponsive', () => ({
  useResponsive: () => ({
    isMobile: false,
    isTablet: false,
    isDesktop: true,
    isLargeDesktop: false,
    currentBreakpoint: 'md',
    spacing: vi.fn((factor: number, factor2?: number) => {
      if (factor2 !== undefined) {
        return `${factor * 8}px ${factor2 * 8}px`;
      }
      return `${factor * 8}px`;
    }),
    fontSize: vi.fn((size: 'small' | 'medium' | 'large') => {
      const sizes = { small: '1rem', medium: '1.25rem', large: '1.5rem' };
      return sizes[size];
    }),
    padding: vi.fn((size: 'small' | 'medium' | 'large') => {
      const sizes = { small: 2, medium: 4, large: 6 };
      return sizes[size];
    }),
    borderRadius: vi.fn((size: 'small' | 'medium' | 'large') => {
      const sizes = { small: 4, medium: 8, large: 12 };
      return sizes[size];
    }),
  }),
}));

describe('Utility Hooks', () => {
  describe('useScroll', () => {
    beforeEach(() => {
      // Mock window.scrollTo and requestAnimationFrame
      window.scrollTo = vi.fn();
      global.requestAnimationFrame = vi.fn(callback => {
        callback();
        return 1;
      });
    });

    afterEach(() => {
      vi.restoreAllMocks();
    });

    test('returns container ref and scroll functions', () => {
      const { result } = renderHook(() => useScroll());

      expect(result.current.containerRef).toBeDefined();
      expect(result.current.scrollToBottom).toBeDefined();
      expect(result.current.isNearBottom).toBeDefined();
      expect(result.current.scrollToBottomIfNeeded).toBeDefined();
      expect(typeof result.current.scrollToBottom).toBe('function');
      expect(typeof result.current.isNearBottom).toBe('function');
      expect(typeof result.current.scrollToBottomIfNeeded).toBe('function');
    });

    test('scrolls to bottom', () => {
      const { result } = renderHook(() => useScroll());

      // Mock container ref
      const mockContainer = {
        scrollHeight: 1000,
        scrollTo: vi.fn(),
      };
      result.current.containerRef.current = mockContainer as any;

      act(() => {
        result.current.scrollToBottom('smooth');
      });

      expect(mockContainer.scrollTo).toHaveBeenCalledWith({
        top: 1000,
        behavior: 'smooth',
      });
    });

    test('scrolls to bottom with default behavior', () => {
      const { result } = renderHook(() => useScroll());

      const mockContainer = {
        scrollHeight: 1000,
        scrollTo: vi.fn(),
      };
      result.current.containerRef.current = mockContainer as any;

      act(() => {
        result.current.scrollToBottom();
      });

      expect(mockContainer.scrollTo).toHaveBeenCalledWith({
        top: 1000,
        behavior: 'smooth',
      });
    });

    test('checks if near bottom', () => {
      const { result } = renderHook(() => useScroll());

      // Mock container near bottom
      const mockContainer = {
        scrollTop: 900,
        scrollHeight: 1000,
        clientHeight: 100,
      };
      result.current.containerRef.current = mockContainer as any;

      const isNear = result.current.isNearBottom();
      expect(isNear).toBe(true);
    });

    test('checks if not near bottom', () => {
      const { result } = renderHook(() => useScroll());

      // Mock container far from bottom
      const mockContainer = {
        scrollTop: 500,
        scrollHeight: 1000,
        clientHeight: 100,
      };
      result.current.containerRef.current = mockContainer as any;

      const isNear = result.current.isNearBottom();
      expect(isNear).toBe(false);
    });

    test('scrolls to bottom if needed when near bottom', () => {
      const { result } = renderHook(() => useScroll());

      const mockContainer = {
        scrollTo: vi.fn(),
        scrollTop: 900,
        scrollHeight: 1000,
        clientHeight: 100,
      };
      result.current.containerRef.current = mockContainer as any;

      act(() => {
        result.current.scrollToBottomIfNeeded(5);
      });

      expect(mockContainer.scrollTo).toHaveBeenCalledWith({
        top: 1000,
        behavior: 'smooth',
      });
    });

    test('does not scroll to bottom if not near bottom', () => {
      const { result } = renderHook(() => useScroll());

      const mockContainer = {
        scrollTo: vi.fn(),
        scrollTop: 500,
        scrollHeight: 1000,
        clientHeight: 100,
      };
      result.current.containerRef.current = mockContainer as any;

      // Call isNearBottom first to update the internal ref
      const isNear = result.current.isNearBottom();
      expect(isNear).toBe(false);

      act(() => {
        result.current.scrollToBottomIfNeeded(5);
      });

      expect(mockContainer.scrollTo).not.toHaveBeenCalled();
    });

    test('uses auto behavior for large message counts', () => {
      const { result } = renderHook(() => useScroll());

      const mockContainer = {
        scrollTo: vi.fn(),
        scrollTop: 900,
        scrollHeight: 1000,
        clientHeight: 100,
      };
      result.current.containerRef.current = mockContainer as any;

      act(() => {
        result.current.scrollToBottomIfNeeded(25);
      });

      expect(mockContainer.scrollTo).toHaveBeenCalledWith({
        top: 1000,
        behavior: 'auto',
      });
    });

    test('respects custom threshold', () => {
      const { result } = renderHook(() => useScroll({ threshold: 50 }));

      const mockContainer = {
        scrollTop: 920,
        scrollHeight: 1000,
        clientHeight: 100,
      };
      result.current.containerRef.current = mockContainer as any;

      const isNear = result.current.isNearBottom();
      expect(isNear).toBe(true);
    });

    test('handles null container gracefully', () => {
      const { result } = renderHook(() => useScroll());

      result.current.containerRef.current = null;

      const isNear = result.current.isNearBottom();
      expect(isNear).toBe(true);

      act(() => {
        result.current.scrollToBottom();
      });

      // Should not throw error
    });
  });
});
