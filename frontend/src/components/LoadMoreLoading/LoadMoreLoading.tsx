import { Box, CircularProgress } from '@mui/material';

function LoadMoreLoading() {
  return (
    <Box sx={{ display: 'flex', justifyContent: 'center', my: 2 }}>
      <CircularProgress size={24} disableShrink />
    </Box>
  );
}

export default LoadMoreLoading;
