import { Box, Drawer } from '@mui/material';
import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { Outlet, useLocation, useNavigate, useParams } from 'react-router-dom';
import {
  createSession,
  deleteSessionBySessionId,
  getSessionsListByUserId,
  updateSessionTitle,
} from '@/services/api';
import { enqueueSnackbar } from 'notistack';
import { useAuth } from '@/hooks/useAuth';
import { useSession } from '@/hooks/useSession';
import debounce from 'lodash.debounce';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import DeleteDialog from '@/components/DeleteDialog/DeleteDialog';
import ChatSessionsList from '@/components/Layout/ChatSessionsList';
import SessionMenu from '@/components/Layout/SessionMenu';
import SidebarDrawer from '@/components/Layout/SidebarDrawer';
import Header from '@/components/Layout/Header';
import { routes } from '@/constants/routes';

export const drawerWidth = 240;

export default function Layout() {
  const [mobileOpen, setMobileOpen] = useState<boolean>(false);
  const [isClosing, setIsClosing] = useState<boolean>(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();
  const [, setChatPage] = useState<number>(0);
  const [chatLimit] = useState<number>(20);
  const {
    sessions: chatSessions,
    loading,
    initialLoading,
    hasMore,
    setSessions,
    addSessions,
    addSession,
    removeSessionById,
    setLoading,
    setInitialLoading,
    setHasMore,
    updateSession,
  } = useSession();
  const { sessionId } = useParams<{ sessionId: string }>();
  const [clickChatId, setClickChatId] = useState<string | undefined>(sessionId);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState<boolean>(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [openEditTitleDialog, setOpenEditTitleDialog] = useState<boolean>(false);
  const { t: tChat } = useTranslations('chat');

  const observer = useRef<IntersectionObserver | null>(null);
  const chatListRef = useRef<HTMLDivElement | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  const { isChatScreen, currentTitle } = useMemo(() => {
    const pathName = location.pathname;
    const isChatScreen = pathName.startsWith('/chat');

    let title = 'navigation.userManagement';
    if (isChatScreen) {
      title = 'navigation.chat';
    } else if (pathName === '/') {
      title = 'navigation.userManagement';
    }

    return { isChatScreen, currentTitle: title };
  }, [location.pathname]);

  const handleDrawerClose = () => {
    setIsClosing(true);
    setMobileOpen(false);
  };

  useEffect(() => {
    setClickChatId(sessionId);
  }, [sessionId]);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  const handleNewChat = debounce(async () => {
    try {
      if (!user?.userId) return;

      const result = await createSession(user.userId);
      if (result && result.status === 200) {
        navigate(routes.chatSession.replace(':sessionId', result.data.session_id));
        addSession(result.data);
      }
    } catch (error: any) {
      console.log(error);
      enqueueSnackbar(`${error.response?.data?.detail || tChat('session.create.error')}`, {
        variant: 'error',
      });
    }
  }, 500);

  const fetchSessions = useCallback(
    async (page: number, append: boolean = false) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      abortControllerRef.current = new AbortController();

      if (!user?.userId) return;
      if (loading && append) return;

      try {
        setLoading(true);
        if (!append) {
          setInitialLoading(true);
        }

        const result = await getSessionsListByUserId(
          user.userId,
          page,
          chatLimit,
          abortControllerRef.current.signal
        );

        if (result?.status === 200) {
          const newSessions = result.data.sessions || [];

          if (append) {
            const uniqueSessionIds = new Set(chatSessions.map((s) => s.session_id));
            const filteredNewSessions = newSessions.filter(
              (session) => !uniqueSessionIds.has(session.session_id)
            );
            addSessions(filteredNewSessions);
          } else {
            setSessions(newSessions);
          }

          setHasMore(newSessions.length === chatLimit);
        }
      } catch (error: any) {
        if (error.name !== 'AbortError') {
          console.error('Error fetching sessions:', error);
        }
      } finally {
        setLoading(false);
        setInitialLoading(false);
      }
    },
    [user?.userId, chatLimit, chatSessions, setLoading, setInitialLoading, setHasMore]
  );

  const resetAndFetchSessions = useCallback(() => {
    setChatPage(0);
    setHasMore(true);
    setSessions([]);
    fetchSessions(0, false);
  }, [user?.userId]);

  const handleDeleteSession = async () => {
    try {
      if (!currentSessionId) return;

      setDeleteDialogOpen(false);

      const result = await deleteSessionBySessionId(currentSessionId);

      cancelDelete();
      if (result && result.status === 200) {
        removeSessionById(currentSessionId);
        enqueueSnackbar(tChat('session.delete.success'), {
          variant: 'success',
        });
        if (location.pathname === routes.chatSession.replace(':sessionId', currentSessionId)) {
          navigate(routes.chat);
        }
      }
    } catch (error: any) {
      console.log(error);
      enqueueSnackbar(`${error.response?.data?.detail || tChat('session.delete.error')}`, {
        variant: 'error',
      });
    }
  };

  useEffect(() => {
    if (isChatScreen && user?.userId) {
      resetAndFetchSessions();
    }
  }, [isChatScreen, user?.userId, resetAndFetchSessions]);

  const debouncedFetchSessions = useMemo(() => {
    return debounce((page: number, append: boolean = false) => {
      fetchSessions(page, append);
    }, 100); // 100ms debounce
  }, [fetchSessions]);

  const lastChatElementRef = useCallback(
    (node: HTMLDivElement | null) => {
      if (initialLoading || loading || !hasMore) return;

      if (observer.current) observer.current.disconnect();

      observer.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            setChatPage((prevPage) => {
              const nextPage = prevPage + 1;
              debouncedFetchSessions(nextPage, true);
              return nextPage;
            });
          }
        },
        {
          threshold: 0.1, // Load even earlier
          rootMargin: '200px', // Increased margin to load more eagerly
        }
      );

      if (node) observer.current.observe(node);
    },
    [loading, initialLoading, hasMore, debouncedFetchSessions]
  );

  const handleChatSelect = useCallback(
    (chatId: string) => {
      navigate(routes.chatSession.replace(':sessionId', chatId));
      setClickChatId(chatId);

      if (mobileOpen) {
        handleDrawerClose();
      }
    },
    [navigate, mobileOpen]
  );

  const handleDrawerTransitionEnd = () => {
    setIsClosing(false);
  };

  const handleDrawerToggle = () => {
    if (!isClosing) {
      setMobileOpen(!mobileOpen);
    }
  };

  const handleNavigate = useCallback(
    (path: string) => {
      navigate(path);

      if (mobileOpen) {
        handleDrawerClose();
      }
    },
    [navigate, mobileOpen]
  );

  const cancelDelete = () => {
    setDeleteDialogOpen(false);
    setCurrentSessionId(null);
  };

  const openDeleteDialog = useCallback((event: React.MouseEvent) => {
    event.stopPropagation();
    setDeleteDialogOpen(true);
  }, []);

  const handleMenuOpen = useCallback((event: React.MouseEvent<HTMLElement>, sessionId: string) => {
    event.stopPropagation();
    setAnchorEl(event.currentTarget);
    setCurrentSessionId(sessionId);
  }, []);

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleEditDialogClose = () => {
    setOpenEditTitleDialog(false);
    setCurrentSessionId(null);
  };

  const handleEditDialogOpen = useCallback((e: React.MouseEvent<HTMLLIElement>) => {
    e.stopPropagation();
    setAnchorEl(null);
    setOpenEditTitleDialog(true);
  }, []);

  const handleSaveSessionTitle = async (title: string) => {
    try {
      if (!currentSessionId) return;

      setOpenEditTitleDialog(false);

      const result = await updateSessionTitle({
        name: title,
        session_id: currentSessionId,
      });

      handleEditDialogClose();
      if (result && result.status === 200) {
        enqueueSnackbar(tChat('session.edit.title.success'), {
          variant: 'success',
        });

        const session = chatSessions.find((session) => session.session_id === currentSessionId);

        updateSession(currentSessionId, {
          ...session,
          name: title,
        });
      }
    } catch (error: any) {
      console.log(error);
      enqueueSnackbar(`${error.response?.data?.detail || tChat('session.edit.title.error')}`, {
        variant: 'error',
      });
    }
  };

  const handleDeleteDialogOpen = useCallback(
    (e: React.MouseEvent<HTMLLIElement>) => {
      e.stopPropagation();
      setAnchorEl(null);
      openDeleteDialog(e);
    },
    [openDeleteDialog]
  );

  const chatSessionsList = useMemo(
    () => (
      <ChatSessionsList
        clickChatId={clickChatId}
        handleChatSelect={handleChatSelect}
        handleMenuOpen={handleMenuOpen}
        lastChatElementRef={lastChatElementRef}
        handleNewChat={handleNewChat}
      />
    ),
    [
      chatSessions,
      clickChatId,
      loading,
      hasMore,
      handleChatSelect,
      handleMenuOpen,
      lastChatElementRef,
      handleNewChat,
    ]
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <Header currentTitle={currentTitle} handleDrawerToggle={handleDrawerToggle} />
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
        aria-label="menu"
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onTransitionEnd={handleDrawerTransitionEnd}
          onClose={handleDrawerClose}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
            },
            scrollbarWidth: 'none',
          }}
        >
          <SidebarDrawer
            handleNavigate={handleNavigate}
            isChatScreen={isChatScreen}
            handleNewChat={handleNewChat}
            initialLoading={initialLoading}
            chatSessionsList={chatSessionsList}
            chatListRef={chatListRef}
            openEditTitleDialog={openEditTitleDialog}
            currentSessionId={currentSessionId}
            chatSessions={chatSessions}
            handleEditDialogClose={handleEditDialogClose}
            handleSaveSessionTitle={handleSaveSessionTitle}
          />
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': {
              boxSizing: 'border-box',
              width: drawerWidth,
              borderRight: '1px solid #e0e0e0',
              scrollbarWidth: 'none',
            },
          }}
          open
        >
          <SidebarDrawer
            handleNavigate={handleNavigate}
            isChatScreen={isChatScreen}
            handleNewChat={handleNewChat}
            initialLoading={initialLoading}
            chatSessionsList={chatSessionsList}
            chatListRef={chatListRef}
            openEditTitleDialog={openEditTitleDialog}
            currentSessionId={currentSessionId}
            chatSessions={chatSessions}
            handleEditDialogClose={handleEditDialogClose}
            handleSaveSessionTitle={handleSaveSessionTitle}
          />
        </Drawer>
      </Box>
      <Outlet />
      <SessionMenu
        anchorEl={anchorEl}
        handleMenuClose={handleMenuClose}
        handleEditDialogOpen={handleEditDialogOpen}
        handleDeleteDialogOpen={handleDeleteDialogOpen}
      />
      <DeleteDialog
        deleteDialogOpen={deleteDialogOpen}
        cancelDelete={cancelDelete}
        confirmDelete={handleDeleteSession}
        title={tChat('session.delete.confirm')}
        description={tChat('session.delete.warning')}
      />
    </Box>
  );
}
