import {
  Avatar,
  Box,
  Button,
  Divider,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Toolbar,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add, LogoutOutlined as LogoutOutlinedIcon } from '@mui/icons-material';
import React, { memo, useMemo } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useLocation, useNavigate } from 'react-router-dom';
import PeopleIcon from '@mui/icons-material/People';
import ChatIcon from '@mui/icons-material/Chat';
import TessLogo from '@/components/Layout/TessLogo';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import EditTitleDialog from '@/components/Layout/EditTitleDialog';
import { SessionType } from '@/types/types';
import { routes } from '@/constants/routes';
import LoadMoreLoading from '../LoadMoreLoading/LoadMoreLoading';

interface SidebarDrawerProps {
  handleNavigate: (path: string) => void;
  isChatScreen: boolean;
  handleNewChat: () => void;
  initialLoading: boolean;
  chatSessionsList: React.ReactNode;
  chatListRef: React.RefObject<HTMLDivElement | null>;
  openEditTitleDialog: boolean;
  currentSessionId: string | null;
  chatSessions: SessionType[];
  handleEditDialogClose: () => void;
  handleSaveSessionTitle: (title: string) => void;
}

const SidebarDrawer: React.FC<SidebarDrawerProps> = ({
  handleNavigate,
  isChatScreen,
  handleNewChat,
  initialLoading,
  chatSessionsList,
  chatListRef,
  openEditTitleDialog,
  currentSessionId,
  chatSessions,
  handleEditDialogClose,
  handleSaveSessionTitle,
}) => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const { t } = useTranslations('common');
  const { t: tChat } = useTranslations('chat');
  const location = useLocation();
  const initialTitle =
    currentSessionId && chatSessions.find((s) => s.session_id === currentSessionId)?.name;

  const MenuItems = useMemo(
    () => [
      {
        label: 'navigation.users',
        icon: <PeopleIcon />,
        active: location.pathname === routes.home,
        path: routes.home,
      },
      {
        label: 'navigation.chats',
        icon: <ChatIcon />,
        active:
          location.pathname === routes.chat || location.pathname.startsWith(routes.chatSession),
        path: routes.chat,
      },
    ],
    [location.pathname]
  );

  return (
    <Box>
      <EditTitleDialog
        onClose={handleEditDialogClose}
        onSave={handleSaveSessionTitle}
        open={openEditTitleDialog}
        initialTitle={initialTitle!}
      />
      <Toolbar
        sx={{
          justifyContent: 'center',
          cursor: 'pointer',
          minHeight: { md: '62px' },
        }}
        onClick={() => navigate(routes.home)}
      >
        <TessLogo />
      </Toolbar>
      <Divider />
      <Box sx={{ mt: 2, mb: 1, px: 2 }}>
        <Typography variant="body2" color="textSecondary">
          {t('general.menu')}
        </Typography>
      </Box>
      <List>
        {MenuItems.map(({ icon, label, active, path }) => (
          <ListItem key={label} disablePadding sx={{ my: 0.5 }}>
            <ListItemButton
              sx={{
                backgroundColor: active ? '#f0f4f8' : 'transparent',
                borderRadius: '4px',
                mx: 1,
              }}
              onClick={() => handleNavigate(path)}
            >
              <ListItemIcon>{icon}</ListItemIcon>
              <ListItemText primary={t(label)} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {isChatScreen && (
        <>
          <Box
            sx={{
              mb: 1,
              px: 2,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
            }}
          >
            <Typography variant="body2" color="textSecondary">
              {t('navigation.chats')}
            </Typography>
            <Tooltip title={tChat('session.create.button')} disableInteractive>
              <IconButton size="small" onClick={handleNewChat} sx={{ color: 'primary.main' }}>
                <Add fontSize="small" />
              </IconButton>
            </Tooltip>
          </Box>
          <Box
            ref={chatListRef}
            sx={{
              px: 1,
              maxHeight:  'calc(100vh - 450px)' ,
              overflowY: 'auto',
              overscrollBehavior: 'contain',
              willChange: 'transform',
              '&::-webkit-scrollbar': {
                width: '4px',
              },
              '&::-webkit-scrollbar-thumb': {
                backgroundColor: 'rgba(0,0,0,0.2)',
                borderRadius: '4px',
              },
              '&::-webkit-scrollbar-track': {
                backgroundColor: 'transparent',
              },
            }}
          >
            {initialLoading ? <LoadMoreLoading /> : chatSessionsList}
          </Box>
        </>
      )}

      <Box sx={{ position: 'fixed', bottom: 0, width: 240 }}>
        <Box sx={{ mt: 1, px: 2 }}>
          <Typography variant="body2" color="textSecondary">
            {t('navigation.profile')}
          </Typography>
        </Box>
        <List>
          <ListItem>
            <ListItemIcon>
              <Avatar sx={{ bgcolor: '#1976d2' }}>
                {user?.userName?.charAt(0).toUpperCase() || t('form.user')}
              </Avatar>
            </ListItemIcon>
            <ListItemText
              primary={user?.userName || t('form.user')}
              secondary={user?.email || ''}
              slotProps={{
                primary: { noWrap: true },
                secondary: { noWrap: true },
              }}
            />
          </ListItem>
          <ListItem sx={{ px: 2, mt: 1 }}>
            <Button
              variant="outlined"
              startIcon={<LogoutOutlinedIcon />}
              fullWidth
              onClick={() => {
                logout();
                navigate(routes.login, { replace: true });
              }}
              sx={{
                justifyContent: 'flex-start',
                color: 'text.primary',
                borderColor: 'divider',
              }}
            >
              {t('auth.logOut')}
            </Button>
          </ListItem>
        </List>
      </Box>
    </Box>
  );
};

export default memo(SidebarDrawer);
