import { MessagesType } from '@/types/types';
import { Box } from '@mui/material';
import { TFunction } from 'i18next';
import ChatSkeleton from './ChatSkeleton';
import LoadMoreLoading from '../LoadMoreLoading/LoadMoreLoading';
import EmptyChat from './EmptyChat';
import Message from './Message';
import Loader from './Loader';
import { memo, RefObject, Dispatch, SetStateAction } from 'react';

function ChatMessages({
  messagesContainerRef,
  messagesEndRef,
  sessionLoading,
  loadingMore,
  isCurrentSessionLoading,
  Data,
  isMobile,
  tChat,
  setLocalData,
}: {
  messagesContainerRef: RefObject<HTMLDivElement | null>;
  messagesEndRef: RefObject<HTMLDivElement | null>;
  sessionLoading: boolean;
  loadingMore: boolean;
  isCurrentSessionLoading: boolean;
  Data: MessagesType[];
  isMobile: boolean;
  tChat: TFunction<'common' | 'auth' | 'users' | 'chat', undefined>;
  setLocalData: Dispatch<SetStateAction<Record<string, MessagesType[]>>>;
}) {
  return (
    <Box
      ref={messagesContainerRef}
      sx={{
        flexGrow: 1,
        overflow: 'auto',
        p: 3,
        display: 'flex',
        flexDirection: 'column',
        '&::-webkit-scrollbar': {
          width: '6px',
        },
        '&::-webkit-scrollbar-track': {
          background: 'rgba(0,0,0,0.1)',
          borderRadius: '3px',
        },
        '&::-webkit-scrollbar-thumb': {
          background: 'rgba(0,0,0,0.3)',
          borderRadius: '3px',
          '&:hover': {
            background: 'rgba(0,0,0,0.5)',
          },
        },
      }}
    >
      {sessionLoading ? (
        <ChatSkeleton />
      ) : (
        <>
          {loadingMore && <LoadMoreLoading />}

          {!isCurrentSessionLoading && Data.length === 0 && <EmptyChat tChat={tChat} />}

          {Data.length > 0 &&
            Data.map((msg, i) => (
              <Message isMobile={isMobile} msg={msg} key={i} setLocalData={setLocalData} />
            ))}

          {isCurrentSessionLoading && <Loader isMobile={isMobile} tChat={tChat} />}

          <div ref={messagesEndRef} />
        </>
      )}
    </Box>
  );
}

export default memo(ChatMessages);
