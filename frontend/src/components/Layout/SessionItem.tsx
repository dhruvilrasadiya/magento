import { Box, IconButton, ListItem, ListItemButton, Typography, Tooltip } from '@mui/material';
import { styled } from '@mui/material/styles';
import { MoreVert } from '@mui/icons-material';
import React, { memo } from 'react';
import { SessionType } from '@/types/types';
import { useTranslations } from '@/i18n/hooks/useTranslations';

// Styled components for better performance
const StyledListItem = styled(ListItem)(({ theme }) => ({
  position: 'relative',
  margin: theme.spacing(0.5, 0),
  '&:hover .delete-btn': {
    opacity: 1,
    pointerEvents: 'auto',
    background: '#FFF',
    borderRadius: 50,
  },
}));

const StyledDeleteBtn = styled(Box)(() => ({
  position: 'absolute',
  right: 8,
  top: '50%',
  transform: 'translateY(-50%)',
  opacity: 0,
  pointerEvents: 'none',
  transition: 'opacity 0.2s ease',
}));

const SessionItem = React.memo(
  ({
    session,
    isSelected,
    onSelect,
    onMenuOpen,
    isLastElement,
    listRef,
  }: {
    session: SessionType;
    isSelected: boolean;
    onSelect: (id: string) => void;
    onMenuOpen: (event: React.MouseEvent<HTMLElement>, id: string) => void;
    isLastElement: boolean;
    listRef: (node: HTMLDivElement | null) => void;
  }) => {
    const { t: tChat } = useTranslations('chat');
    return (
      <div ref={isLastElement ? listRef : null}>
        <Tooltip
          title={session?.name || tChat('session.create.new')}
          placement="right"
          arrow
          disableInteractive
        >
          <StyledListItem disablePadding>
            <ListItemButton
              onClick={() => onSelect(session.session_id)}
              sx={{
                borderRadius: '8px',
                backgroundColor: isSelected ? '#f0f4f8' : 'transparent',
                '&:hover': {
                  backgroundColor: isSelected ? '#e3eaf2' : '#f5f5f5',
                },
              }}
            >
              <Box sx={{ width: '100%', paddingY: 1 }}>
                <Typography
                  variant="body2"
                  noWrap
                  sx={{
                    fontWeight: isSelected ? 600 : 400,
                    color: 'text.primary',
                  }}
                >
                  {session?.name || tChat('session.create.new')}
                </Typography>
              </Box>
            </ListItemButton>

            <StyledDeleteBtn className="delete-btn">
              <IconButton
                size="small"
                onClick={(e) => onMenuOpen(e, session.session_id)}
                sx={{
                  backgroundColor: 'rgba(255,255,255,0.8)',
                  '&:hover': {
                    backgroundColor: 'rgba(255,255,255,0.9)',
                  },
                }}
              >
                <MoreVert fontSize="small" />
              </IconButton>
            </StyledDeleteBtn>
          </StyledListItem>
        </Tooltip>
      </div>
    );
  }
);

export default memo(SessionItem);
