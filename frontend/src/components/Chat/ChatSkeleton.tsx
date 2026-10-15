import { Box, Skeleton, useMediaQuery, useTheme } from '@mui/material';

const ChatSkeleton = () => {
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'));

  return (
    <Box sx={{ width: '100%' }}>
      {[1, 2, 3, 4].map((i) => (
        <Box
          key={i}
          sx={{
            display: 'flex',
            justifyContent: i % 2 === 0 ? 'flex-end' : 'flex-start',
            mb: 2,
          }}
        >
          <Skeleton
            variant="rectangular"
            width={isMobile ? '70%' : '40%'}
            height={60}
            sx={{
              borderRadius: '10px',
              bgcolor: i % 2 === 0 ? '#e0e0e0' : '#d0d9ff',
            }}
          />
        </Box>
      ))}
    </Box>
  );
};

export default ChatSkeleton;
