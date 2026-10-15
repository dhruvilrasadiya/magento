import { useEffect, useRef, useState, useCallback, useMemo, JSX } from 'react';
import { Box, useTheme, useMediaQuery } from '@mui/material';
import { createSession, getSessionBySessionId, sendQuery } from '@/services/api';
import { MessagesType, SendQueryApiPayload } from '@/types/types';
import { enqueueSnackbar } from 'notistack';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { useSession } from '@/hooks/useSession';
import i18next from 'i18next';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import { routes } from '@/constants/routes';
import ChatInput from '@/components/Chat/ChatInput';
import ChatMessages from '@/components/Chat/ChatMessages';
import { Email, Inbox } from '@mui/icons-material';

const MESSAGES_PER_PAGE = 100;
const SCROLL_THRESHOLD = 50;
const FAB_THRESHOLD = 100;

const globalSessionData: Record<string, MessagesType[]> = {};
const globalLoadingStates: Record<
  string,
  {
    sessionLoading: boolean;
    loadingMore: boolean;
    sendingMessage: boolean;
    hasMore: boolean;
    currentPage: number;
    isInitialized: boolean;
  }
> = {};

const activeRequests = new Set<string>();

function debounce<T extends (...args: any[]) => void>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

export const COMMAND_OPTIONS: {
  id: string;
  icon: JSX.Element;
  label: string;
  value: string;
  bgcolor?: string;
}[] = [
  {
    id: 'email',
    icon: <Email fontSize="small" sx={{ mr: 1, color: '#5b7bc0' }} />,
    label: 'commandOptions.email',
    value: '/email',
    bgcolor: '',
  },
  {
    id: 'inbox',
    icon: <Inbox fontSize="small" sx={{ mr: 1, color: '#5b7bc0' }} />,
    label: 'commandOptions.inbox',
    value: '/inbox',
    bgcolor: '',
  },
];

const Chat = () => {
  const [message, setMessage] = useState('');
  const [showScrollToBottom, setShowScrollToBottom] = useState(false);
  const [localData, setLocalData] = useState<Record<string, MessagesType[]>>({});
  const [localLoadingStates, setLocalLoadingStates] = useState<typeof globalLoadingStates>({});
  const [selectedOption, setSelectedOption] = useState<(typeof COMMAND_OPTIONS)[0] | null>(null);
  const [isAutoSendEmail, setIsAutoSendEmail] = useState<boolean>(false);

  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const previousScrollHeightRef = useRef<number>(0);
  const autoScrollRef = useRef<boolean>(true);

  const { sessionId } = useParams<{ sessionId?: string }>();
  const { user } = useAuth();
  const { addSession, updateSession, sessions: chatSessions } = useSession();
  const navigate = useNavigate();
  const { t: tChat } = useTranslations('chat');

  useEffect(() => {
    setLocalData({ ...globalSessionData });
    setLocalLoadingStates({ ...globalLoadingStates });
  }, [sessionId]);

  const updateGlobalData = useCallback((sessionId: string, messages: MessagesType[]) => {
    globalSessionData[sessionId] = messages;
    setLocalData((prev) => ({ ...prev, [sessionId]: messages }));
  }, []);

  const updateGlobalLoadingState = useCallback(
    (sessionId: string, updates: Partial<(typeof globalLoadingStates)[string]>) => {
      globalLoadingStates[sessionId] = {
        ...globalLoadingStates[sessionId],
        ...updates,
      };
      setLocalLoadingStates((prev) => ({
        ...prev,
        [sessionId]: globalLoadingStates[sessionId],
      }));
    },
    []
  );

  const currentSessionState = useMemo(() => {
    if (!sessionId)
      return {
        messages: [],
        sessionLoading: false,
        loadingMore: false,
        sendingMessage: false,
        hasMore: true,
        currentPage: 0,
        isInitialized: false,
      };

    const defaultState = {
      sessionLoading: true,
      loadingMore: false,
      sendingMessage: false,
      hasMore: true,
      currentPage: 0,
      isInitialized: false,
    };

    return {
      messages: localData[sessionId] || globalSessionData[sessionId] || [],
      ...(localLoadingStates[sessionId] || globalLoadingStates[sessionId] || defaultState),
    };
  }, [localData, localLoadingStates, sessionId]);

  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        block: 'end',
        inline: 'nearest',
      });
      setShowScrollToBottom(false);
    }
  }, []);

  const checkScrollPosition = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    const { scrollTop, scrollHeight, clientHeight } = container;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    const isNear = distanceFromBottom <= FAB_THRESHOLD;

    setShowScrollToBottom(!isNear && currentSessionState.messages.length > 0);
  }, [currentSessionState.messages.length]);

  const fetchMessages = async (targetSessionId: string, page: number) => {
    const requestKey = `${targetSessionId}-${page}`;
    if (activeRequests.has(requestKey)) return;

    activeRequests.add(requestKey);
    const isInitialLoad = page === 0;

    try {
      if (isInitialLoad) {
        updateGlobalLoadingState(targetSessionId, { sessionLoading: true });
      } else {
        updateGlobalLoadingState(targetSessionId, { loadingMore: true });
        if (messagesContainerRef.current) {
          previousScrollHeightRef.current = messagesContainerRef.current.scrollHeight;
        }
      }

      const skip = page * MESSAGES_PER_PAGE;
      const result = await getSessionBySessionId(targetSessionId, skip, MESSAGES_PER_PAGE);

      if (result?.status === 200 && result.data.messages) {
        const newMessages = result.data.messages || [];
        const hasMoreData = newMessages.length >= MESSAGES_PER_PAGE;
        const existingMessages = globalSessionData[targetSessionId] || [];

        const updatedMessages = isInitialLoad ? newMessages : [...newMessages, ...existingMessages];

        updateGlobalData(targetSessionId, updatedMessages);
        updateGlobalLoadingState(targetSessionId, {
          hasMore: hasMoreData,
          currentPage: page + 1,
          isInitialized: true,
        });

        if (!isInitialLoad && messagesContainerRef.current) {
          requestAnimationFrame(() => {
            if (messagesContainerRef.current) {
              const newScrollHeight = messagesContainerRef.current.scrollHeight;
              const scrollDifference = newScrollHeight - previousScrollHeightRef.current;
              messagesContainerRef.current.scrollTop = scrollDifference;
            }
          });
        }
      } else if (isInitialLoad) {
        updateGlobalLoadingState(targetSessionId, {
          hasMore: false,
          isInitialized: true,
        });
      }
    } catch (error) {
      const errorMessage = isInitialLoad
        ? tChat('fetchMessages.error')
        : 'Failed to load more messages';

      enqueueSnackbar(errorMessage, { variant: 'error' });

      if (isInitialLoad) {
        updateGlobalLoadingState(targetSessionId, {
          hasMore: false,
          isInitialized: true,
        });
      }
    } finally {
      activeRequests.delete(requestKey);
      updateGlobalLoadingState(targetSessionId, {
        sessionLoading: false,
        loadingMore: false,
      });
    }
  };

  const debouncedFetchMessages = useCallback(
    debounce((targetSessionId: string, page: number) => {
      fetchMessages(targetSessionId, page);
    }, 300),
    [fetchMessages]
  );

  const handleScroll = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container || !sessionId) return;

    checkScrollPosition();

    if (
      currentSessionState.hasMore &&
      !currentSessionState.sessionLoading &&
      !currentSessionState.loadingMore &&
      container.scrollTop <= SCROLL_THRESHOLD
    ) {
      autoScrollRef.current = false;
      debouncedFetchMessages(sessionId, currentSessionState.currentPage);
    }

    const { scrollTop, scrollHeight, clientHeight } = container;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;
    if (distanceFromBottom <= FAB_THRESHOLD) {
      autoScrollRef.current = true;
    }
  }, [sessionId, currentSessionState, checkScrollPosition, debouncedFetchMessages]);

  const handleNewChat = async (shouldNavigate = true) => {
    try {
      const result = await createSession(user?.userId as string);
      if (result?.status === 200) {
        addSession(result.data);

        // Initialize the session data immediately
        globalSessionData[result.data.session_id] = [];
        globalLoadingStates[result.data.session_id] = {
          sessionLoading: false,
          loadingMore: false,
          sendingMessage: false,
          hasMore: true,
          currentPage: 0,
          isInitialized: true,
        };

        if (shouldNavigate) {
          navigate(routes.chatSession.replace(':sessionId', result.data.session_id), {
            replace: true,
          });
        }

        return result.data.session_id;
      }
    } catch (error: any) {
      console.log(error);
      enqueueSnackbar(`${error.response?.data?.detail || tChat('session.create.error')}`, {
        variant: 'error',
      });
    }
  };

  const handleSendMessage = async () => {
    const trimmedMessage = message.trim();
    if (!trimmedMessage) return;

    let newSessionId: string | undefined;
    const currentSessionId = sessionId || '';

    if (!sessionId) {
      newSessionId = await handleNewChat();
      if (!newSessionId) return;
    }

    const activeSessionId = newSessionId || currentSessionId;
    if (!activeSessionId) return;

    updateGlobalLoadingState(activeSessionId, { sendingMessage: true });

    const messageId = `msg_${Date.now()}`;
    const userMessage: MessagesType = {
      id: messageId,
      session_id: activeSessionId,
      message: trimmedMessage,
      response: '',
      metadata: {},
      timestamp: new Date(),
    };

    if (!globalSessionData[activeSessionId]) {
      globalSessionData[activeSessionId] = [];
    }

    const existingMessages = globalSessionData[activeSessionId] || [];
    updateGlobalData(activeSessionId, [...existingMessages, userMessage]);

    setMessage('');
    autoScrollRef.current = true;

    try {
      const query = selectedOption?.value
        ? selectedOption?.value + ' ' + trimmedMessage
        : trimmedMessage;

      const payload: SendQueryApiPayload = {
        query,
        session_id: activeSessionId,
        modal_name: 'gpt-4o-mini',
        stream: false,
        language: i18next.language,
        auto_send_email: isAutoSendEmail,
      };

      const result = await sendQuery(payload);

      if (result?.status === 200) {
        const botMessage: MessagesType = {
          id: result.data.message_id,
          session_id: activeSessionId,
          message: '',
          response: result.data.response,
          metadata: result.data.metadata || {},
          timestamp: new Date(),
        };

        const currentMessages = globalSessionData[activeSessionId] || [];
        updateGlobalData(activeSessionId, [...currentMessages, botMessage]);

        if (result.data?.name) {
          const session = chatSessions.find(
            (session) => session.session_id === result.data.session_id
          );

          updateSession(result.data.session_id, {
            ...session,
            name: result.data.name,
          });
        }
      }
    } catch (error: any) {
      console.log(error);
      setMessage(trimmedMessage);
      enqueueSnackbar(tChat('response.error'), { variant: 'error' });

      const currentMessages = globalSessionData[activeSessionId] || [];
      updateGlobalData(
        activeSessionId,
        currentMessages.filter((msg) => msg.id !== messageId)
      );
    } finally {
      updateGlobalLoadingState(activeSessionId, { sendingMessage: false });
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleScrollToBottomClick = () => {
    autoScrollRef.current = true;
    scrollToBottom();
  };

  useEffect(() => {
    if (
      !currentSessionState.loadingMore &&
      !currentSessionState.sessionLoading &&
      autoScrollRef.current
    ) {
      const timeoutId = setTimeout(scrollToBottom, 100);
      return () => clearTimeout(timeoutId);
    }
  }, [
    currentSessionState.messages.length,
    currentSessionState.loadingMore,
    currentSessionState.sessionLoading,
    scrollToBottom,
  ]);

  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    container.addEventListener('scroll', handleScroll, { passive: true });
    return () => container.removeEventListener('scroll', handleScroll);
  }, [handleScroll]);

  useEffect(() => {
    if (sessionId && !currentSessionState.isInitialized) {
      autoScrollRef.current = true;
      fetchMessages(sessionId, 0);
    }
    // return () => {
    //   if (sessionId && !currentSessionState.sendingMessage) {
    //     delete localLoadingStates[sessionId];
    //     delete localData[sessionId];

    //     delete globalLoadingStates[sessionId];
    //     delete globalSessionData[sessionId];
    //   }
    //   setMessage('');
    // };
  }, [sessionId, currentSessionState.isInitialized]);

  useEffect(() => {
    return () => {
      setMessage('');
      autoScrollRef.current = true;
    };
  }, []);

  return (
    <Box
      sx={{
        height: '100vh',
        display: 'flex',
        flexDirection: 'column',
        width: '100vw',
        pt: 8,
        bgcolor: '#f5f7fa',
      }}
    >
      <ChatMessages
        messagesContainerRef={messagesContainerRef}
        messagesEndRef={messagesEndRef}
        sessionLoading={currentSessionState.sessionLoading}
        loadingMore={currentSessionState.loadingMore}
        isCurrentSessionLoading={currentSessionState.sendingMessage}
        Data={currentSessionState.messages}
        isMobile={isMobile}
        tChat={tChat}
        setLocalData={setLocalData}
      />

      <ChatInput
        message={message}
        setMessage={setMessage}
        handleSendMessage={handleSendMessage}
        handleKeyPress={handleKeyPress}
        isCurrentSessionLoading={currentSessionState.sendingMessage}
        sessionLoading={currentSessionState.sessionLoading}
        handleScrollToBottomClick={handleScrollToBottomClick}
        showScrollToBottom={showScrollToBottom}
        selectedOption={selectedOption}
        setSelectedOption={setSelectedOption}
        setIsAutoSendEmail={setIsAutoSendEmail}
      />
    </Box>
  );
};

export default Chat;
