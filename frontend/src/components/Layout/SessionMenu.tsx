import { Divider, ListItemIcon, ListItemText, Menu, MenuItem } from '@mui/material';
import { DeleteOutline, EditOutlined } from '@mui/icons-material';
import React, { memo } from 'react';
import { useTranslations } from '@/i18n/hooks/useTranslations';

interface SessionMenuProps {
  anchorEl: HTMLElement | null;
  handleMenuClose: () => void;
  handleEditDialogOpen: (e: React.MouseEvent<HTMLLIElement>) => void;
  handleDeleteDialogOpen: (e: React.MouseEvent<HTMLLIElement>) => void;
}

const SessionMenu: React.FC<SessionMenuProps> = ({
  anchorEl,
  handleMenuClose,
  handleEditDialogOpen,
  handleDeleteDialogOpen,
}) => {
  const { t: tChat } = useTranslations('chat');
  const { t: tCommon } = useTranslations('common');

  return (
    <Menu
      id="chat-more-menu"
      anchorEl={anchorEl}
      open={Boolean(anchorEl)}
      onClose={handleMenuClose}
      slotProps={{
        paper: {
          elevation: 3,
          sx: {
            minWidth: 150,
            borderRadius: 1,
            mt: 1,
            overflow: 'visible',
            '&:before': {
              content: '""',
              display: 'block',
              position: 'absolute',
              top: -5,
              right: 14,
              width: 10,
              height: 10,
              bgcolor: 'background.paper',
              transform: 'rotate(45deg)',
              zIndex: 0,
            },
          },
        },
      }}
      transformOrigin={{
        horizontal: 'right',
        vertical: 'top',
      }}
      anchorOrigin={{
        horizontal: 'right',
        vertical: 'bottom',
      }}
    >
      <MenuItem
        onClick={handleEditDialogOpen}
        sx={{
          py: 1,
          px: 2,
          '&:hover': {
            backgroundColor: 'rgba(25, 118, 210, 0.08)',
          },
        }}
      >
        <ListItemIcon sx={{ minWidth: 36 }}>
          <EditOutlined fontSize="small" color="primary" />
        </ListItemIcon>
        <ListItemText primary={tChat('session.menu.edit')} />
      </MenuItem>

      <Divider sx={{ my: 0.5 }} />

      <MenuItem
        onClick={handleDeleteDialogOpen}
        sx={{
          py: 1,
          px: 2,
          '&:hover': {
            backgroundColor: 'rgba(211, 47, 47, 0.08)',
          },
        }}
      >
        <ListItemIcon sx={{ minWidth: 36 }}>
          <DeleteOutline fontSize="small" color="error" />
        </ListItemIcon>
        <ListItemText primary={tCommon('form.delete')} sx={{ color: 'error.main' }} />
      </MenuItem>
    </Menu>
  );
};

export default memo(SessionMenu);
