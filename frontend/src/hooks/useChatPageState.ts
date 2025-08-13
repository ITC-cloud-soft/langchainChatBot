import { useState, useCallback } from 'react';

/**
 * ChatPageの状態管理をカスタムフックに分離して再レンダリングを最適化
 */
export const useChatPageState = () => {
  // 入力メッセージの状態
  const [inputMessage, setInputMessage] = useState('');

  // ナビゲーション関連の状態
  const [activeTab, setActiveTab] = useState('chat');
  const [drawerOpen, setDrawerOpen] = useState(false);

  // 検索関連の状態
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearchLoading, setIsSearchLoading] = useState(false);
  const [searchDialogOpen, setSearchDialogOpen] = useState(false);

  // セッション関連の状態
  const [sessionDialogOpen, setSessionDialogOpen] = useState(false);
  const [sessionDialogTitle, setSessionDialogTitle] = useState('');

  // 入力メッセージをクリアする関数
  const clearInputMessage = useCallback(() => {
    setInputMessage('');
  }, []);

  // 検索結果をクリアする関数
  const clearSearchResults = useCallback(() => {
    setSearchResults([]);
    setSearchQuery('');
  }, []);

  // すべてのダイアログを閉じる関数
  const closeAllDialogs = useCallback(() => {
    setSearchDialogOpen(false);
    setSessionDialogOpen(false);
  }, []);

  return {
    // 入力メッセージ関連
    inputMessage,
    setInputMessage,
    clearInputMessage,

    // ナビゲーション関連
    activeTab,
    setActiveTab,
    drawerOpen,
    setDrawerOpen,

    // 検索関連
    searchQuery,
    setSearchQuery,
    searchResults,
    setSearchResults,
    isSearchLoading,
    setIsSearchLoading,
    searchDialogOpen,
    setSearchDialogOpen,
    clearSearchResults,

    // セッション関連
    sessionDialogOpen,
    setSessionDialogOpen,
    sessionDialogTitle,
    setSessionDialogTitle,

    // ユーティリティ関数
    closeAllDialogs,
  };
};
