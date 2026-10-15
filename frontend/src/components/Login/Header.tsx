import { AppBar, Box, Toolbar } from '@mui/material';
import TessLogo from '@/components/Layout/TessLogo';

function LoginHeader() {
  return (
    <AppBar position="static" variant="outlined" color="inherit" style={{ zIndex: 2 }}>
      <Toolbar variant="dense">
        <Box sx={{ mr: 2, p: 1 }}>
          <TessLogo />
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default LoginHeader;
