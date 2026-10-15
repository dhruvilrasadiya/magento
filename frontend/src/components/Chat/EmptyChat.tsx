import { Box, Typography } from '@mui/material';
import { TFunction } from 'i18next';
import { memo } from 'react';

type Props = {
  tChat: TFunction<'common' | 'auth' | 'users' | 'chat', undefined>;
};

function EmptyChat({ tChat }: Props) {
  return (
    <Box sx={{ textAlign: 'center', mt: 4 }}>
      <Typography variant="body1" color="text.secondary">
        {tChat('conversation.start')}
      </Typography>
    </Box>
  );
}

export default memo(EmptyChat);
