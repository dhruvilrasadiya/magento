import React, { memo } from 'react';
import { Box, Button, List, Typography } from '@mui/material';
import SessionItem from '@/components/Layout/SessionItem';
import { useSession } from '@/hooks/useSession';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import LoadMoreLoading from '../LoadMoreLoading/LoadMoreLoading';

interface ChatSessionsListProps {
  clickChatId: string | undefined;
  handleChatSelect: (sessionId: string) => void;
  handleMenuOpen: (event: React.MouseEvent<HTMLElement>, sessionId: string) => void;
  lastChatElementRef: (node: HTMLDivElement | null) => void;
  handleNewChat: () => void;
}

const ChatSessionsList = ({
  clickChatId,
  handleChatSelect,
  handleMenuOpen,
  lastChatElementRef,
  handleNewChat,
}: ChatSessionsListProps) => {
  const { sessions: chatSessions, loading, hasMore } = useSession();
  const { t: tChat } = useTranslations('chat');

  if (chatSessions.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 4 }}>
        <Typography variant="body2" color="text.secondary">
          {tChat('session.notFound')}
        </Typography>
        <Button variant="outlined" size="small" onClick={handleNewChat} sx={{ mt: 1 }}>
          {tChat('session.create.button')}
        </Button>
      </Box>
    );
  }

  return (
    <List disablePadding>
      {chatSessions.map((chat, index) => (
        <SessionItem
          key={chat.session_id}
          session={chat}
          isSelected={clickChatId === chat.session_id}
          onSelect={handleChatSelect}
          onMenuOpen={handleMenuOpen}
          isLastElement={index === chatSessions.length - 1}
          listRef={lastChatElementRef}
        />
      ))}
      {loading && hasMore && <LoadMoreLoading />}
    </List>
  );
};

export default memo(ChatSessionsList);
