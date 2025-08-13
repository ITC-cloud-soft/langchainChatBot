import { useCallback, startTransition } from 'react';
import { useSnackbar } from 'notistack';
import { chatApi } from '../services/api';

/**
 * ChatPageのイベントハンドラをカスタムフックに分離してパフォーマンスを最適化
 */
export const useChatPageHandlers = (chatPageState: any, chatState: any) => {
  const { enqueueSnackbar } = useSnackbar();
  const { state, actions } = chatState;
  const {
    clearInputMessage,
    closeAllDialogs,
    sessionDialogTitle,
    searchQuery,
    setActiveTab,
    setDrawerOpen,
  } = chatPageState;

  const { selectedSession, sessionId, sessions } = state;

  // セッション一覧を読み込む
  const loadSessions = async () => {
    actions.setSessionsLoading(true);
    try {
      const response = await chatApi.getSessions(1, 50);

      if (response.success) {
        const sessions = response.data.sessions || [];
        actions.setSessions(sessions);
      } else {
        console.error('API response not successful:', response);
      }
    } catch (error) {
      console.error('Failed to load sessions:', error);
      enqueueSnackbar('セッション一覧の読み込みに失敗しました', { variant: 'error' });
      actions.setError('セッション一覧の読み込みに失敗しました');
    }
  };

  // セッションを作成
  const handleCreateSession = useCallback(async () => {
    // ローディング状態を設定
    actions.setSessionsLoading(true);

    try {
      let finalTitle = sessionDialogTitle;

      // タイトルが未入力の場合はデフォルトタイトルを使用（自動生成機能を削除）
      if (!sessionDialogTitle || sessionDialogTitle.trim() === '') {
        finalTitle = '新しいチャット';
      }

      const response = await chatApi.createSession(finalTitle);

      if (response.success) {

        // 楽観的更新：新しいセッションをUIに即座に反映
        const newSession = {
          session_id: response.data.session_id,
          title: response.data.title || finalTitle || '新しいチャット',
          created_at: response.data.created_at,
          updated_at: response.data.created_at, // created_atをupdated_atとして使用
          is_active: true, // デフォルトでアクティブ
        };

        // 状態を更新
        actions.setSessions([...state.sessions, newSession]);
        actions.setSessionId(response.data.session_id);
        actions.clearMessages();

        // ユーザーにフィードバック
        enqueueSnackbar('セッションを作成しました', { variant: 'success' });
        closeAllDialogs();

        // バックグラウンドでセッション一覧を再読み込み（整合性のため）
        try {
          const refreshResponse = await chatApi.getSessions(1, 50);
          if (refreshResponse.success) {
            actions.setSessions(refreshResponse.data.sessions);
          }
        } catch (refreshError) {
          console.warn('Background refresh failed:', refreshError);
          // 楽観的更新が成功しているため、エラーは無視
        }
      } else {
        console.error('Session creation failed:', response);
        enqueueSnackbar('セッションの作成に失敗しました', { variant: 'error' });
      }
    } catch (error) {
      console.error('Session creation error:', error);
      enqueueSnackbar('セッションの作成に失敗しました', { variant: 'error' });
    } finally {
      // ローディング状態を解除
      actions.setSessionsLoading(false);
    }
  }, [
    sessionDialogTitle,
    loadSessions,
    actions,
    enqueueSnackbar,
    closeAllDialogs,
    state.sessions,
    state.messages,
  ]);

  // セッションを選択
  const handleSelectSession = useCallback(
    async (session: any) => {
      // 同じセッションが選択されている場合は何もしない
      if (selectedSession?.session_id === session.session_id) {
        return;
      }

      startTransition(() => {
        actions.setSelectedSession(session);
        actions.setSessionId(session.session_id);
        setActiveTab('chat');
      });

      // セッションのメッセージ履歴を読み込む
      try {
        const response = await chatApi.getFullSession(session.session_id);

        if (response.success) {
          const apiMessages = response.data.messages || [];
          const formattedMessages = Array.isArray(apiMessages)
            ? apiMessages.map((msg: any) => ({
                role: msg.role,
                content: msg.content,
                timestamp: msg.timestamp,
                sourceDocuments: msg.source_documents,
              }))
            : [];

          actions.setMessages(formattedMessages);
        } else {
          console.error('API response not successful:', response);
          enqueueSnackbar('セッションデータの取得に失敗しました', { variant: 'error' });
          actions.setMessages([]);
        }
      } catch (error) {
        console.error('Failed to load session messages:', error);
        enqueueSnackbar('メッセージ履歴の読み込みに失敗しました', { variant: 'error' });
        actions.setMessages([]);
      }
    },
    [actions, enqueueSnackbar, setActiveTab, selectedSession?.session_id],
  );

  // セッションを更新
  const handleUpdateSession = useCallback(
    async (session: any, title?: string) => {
      try {
        let finalTitle = title;

        // タイトルが未入力の場合はデフォルトタイトルを使用（自動生成機能を削除）
        if (!title || title.trim() === '') {
          finalTitle = '新しいチャット';
        }

        // 楽観的更新：UIを即座に更新
        const updatedSessions = state.sessions.map((s: any) =>
          s.session_id === session.session_id
            ? { ...s, title: finalTitle, updated_at: new Date().toISOString() }
            : s,
        );
        actions.setSessions(updatedSessions);

        // 選択中のセッションも更新
        if (selectedSession?.session_id === session.session_id) {
          actions.setSelectedSession({ ...selectedSession, title: finalTitle });
        }

        const response = await chatApi.updateSession(session.session_id, finalTitle);

        if (response.success) {
          enqueueSnackbar('セッションを更新しました', { variant: 'success' });

          // サーバーから最新データを再取得して整合性を確認
          try {
            await loadSessions();
          } catch (refreshError) {
            console.warn('Background refresh failed after update:', refreshError);
            // 楽観的更新が成功しているため、エラーは無視
          }
        } else {
          console.log('API update failed, reverting changes...');
          console.log('API response failure reason:', response.message);
          // 失敗した場合は元に戻す
          await loadSessions();
          enqueueSnackbar(`セッションの更新に失敗しました: ${response.message || '不明なエラー'}`, {
            variant: 'error',
          });
        }
      } catch (error) {
        console.error('Failed to update session:', error);
        // エラー時も最新データを再取得
        await loadSessions();
        enqueueSnackbar('セッションの更新に失敗しました', { variant: 'error' });
      }
    },
    [state.sessions, selectedSession, actions, enqueueSnackbar, loadSessions],
  );

  
  // セッションを削除
  const handleDeleteSession = useCallback(
    async (session: any) => {
      if (
        window.confirm(
          `セッション"${session.title || session.session_id}"を削除してもよろしいですか？`,
        )
      ) {
        try {
          // 楽観的更新：UIから即座に削除
          const filteredSessions = state.sessions.filter((s: any) => s.session_id !== session.session_id);
          actions.setSessions(filteredSessions);

          // 削除対象が選択中のセッションの場合は状態をクリア
          if (sessionId === session.session_id) {
            actions.setSessionId(`session_${Date.now()}`);
            actions.clearMessages();
            actions.setSelectedSession(null);
          }

          const response = await chatApi.deleteSession(session.session_id);

          if (response.success) {
            enqueueSnackbar('セッションを削除しました', { variant: 'success' });

            // サーバーから最新データを再取得して整合性を確認
            try {
              await loadSessions();
            } catch (refreshError) {
              console.warn('Background refresh failed after delete:', refreshError);
              // 楽観的更新が成功しているため、エラーは無視
            }
          } else {
            console.log('API delete failed, reverting changes...');
            // 失敗した場合は元に戻す
            await loadSessions();
            enqueueSnackbar('セッションの削除に失敗しました', { variant: 'error' });
          }
        } catch (error) {
          console.error('Failed to delete session:', error);
          // エラー時も最新データを再取得
          await loadSessions();
          enqueueSnackbar('セッションの削除に失敗しました', { variant: 'error' });
        }
      }
    },
    [state.sessions, sessionId, actions, enqueueSnackbar, loadSessions],
  );

  // ナビゲーションの変更を処理
  const handleNavigationChange = useCallback(
    (tabId: string, isMobile: boolean) => {
      startTransition(() => {
        setActiveTab(tabId);
        if (isMobile) {
          setDrawerOpen(false);
        }
      });
    },
    [setActiveTab, setDrawerOpen],
  );

  return {
    loadSessions,
    handleCreateSession,
    handleSelectSession,
    handleUpdateSession,
    handleDeleteSession,
    handleNavigationChange,
  };
};
