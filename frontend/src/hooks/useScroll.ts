import { useCallback, useEffect, useRef } from 'react';

interface UseScrollProps {
  threshold?: number;
  debounceMs?: number;
}

export const useScroll = ({ threshold = 100, debounceMs = 100 }: UseScrollProps = {}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const isNearBottomRef = useRef(true);
  const lastScrollTimeRef = useRef(0);

  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    if (containerRef.current) {
      requestAnimationFrame(() => {
        containerRef.current?.scrollTo({
          top: containerRef.current.scrollHeight,
          behavior,
        });
      });
    }
  }, []);

  const isNearBottom = useCallback(() => {
    if (!containerRef.current) return true;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const thresholdPixels = threshold;
    const isNear = scrollHeight - scrollTop - clientHeight <= thresholdPixels;

    isNearBottomRef.current = isNear;
    return isNear;
  }, [threshold]);

  const handleScroll = useCallback(() => {
    const now = Date.now();
    if (now - lastScrollTimeRef.current < debounceMs) return;

    lastScrollTimeRef.current = now;
    isNearBottom();
  }, [isNearBottom, debounceMs]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  // メッセージ追加時に自動スクロール
  const scrollToBottomIfNeeded = useCallback(
    (messageCount: number) => {
      if (isNearBottomRef.current) {
        // 少量のメッセージではスムーズスクロール、大量では即時スクロール
        const behavior = messageCount < 20 ? 'smooth' : 'auto';
        scrollToBottom(behavior);
      }
    },
    [scrollToBottom],
  );

  return {
    containerRef,
    scrollToBottom,
    isNearBottom,
    scrollToBottomIfNeeded,
  };
};

// 仮想化リスト用のスクロールフック
interface UseVirtualScrollProps {
  itemHeight: number;
  containerHeight: number;
  overscan?: number;
}

export const useVirtualScroll = ({
  itemHeight,
  containerHeight,
  overscan = 5,
}: UseVirtualScrollProps) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const scrollTopRef = useRef(0);

  const getVisibleRange = useCallback(() => {
    const scrollTop = scrollTopRef.current;
    const startIndex = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
    const endIndex = Math.ceil((scrollTop + containerHeight) / itemHeight) + overscan;

    return { startIndex, endIndex };
  }, [itemHeight, containerHeight, overscan]);

  const handleScroll = useCallback(() => {
    if (containerRef.current) {
      scrollTopRef.current = containerRef.current.scrollTop;
    }
  }, []);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => {
      container.removeEventListener('scroll', handleScroll);
    };
  }, [handleScroll]);

  return {
    containerRef,
    getVisibleRange,
    scrollTop: scrollTopRef.current,
  };
};
