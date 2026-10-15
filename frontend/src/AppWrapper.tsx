import AppRouter from '@/routes/AppRouter';
import './App.css';
import { CssBaseline } from '@mui/material';
import { BrowserRouter } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';

function AppWrapper() {
  return (
    <>
      <CssBaseline />
      <BrowserRouter>
        <SnackbarProvider
          maxSnack={3}
          autoHideDuration={2000}
          anchorOrigin={{ horizontal: 'right', vertical: 'top' }}
        >
          <AppRouter />
        </SnackbarProvider>
      </BrowserRouter>
    </>
  );
}

export default AppWrapper;
