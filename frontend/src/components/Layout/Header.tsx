import React, { memo } from 'react';
import { AppBar, Box, IconButton, Toolbar, Typography } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import { useNavigate } from 'react-router-dom';
import LanguageToggle from '@/components/Layout/LanguageToggle';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import { routes } from '@/constants/routes';

type HeaderProps = {
  currentTitle: string;
  handleDrawerToggle: () => void;
};

const Header: React.FC<HeaderProps> = ({ currentTitle, handleDrawerToggle }) => {
  const navigate = useNavigate();
  const { t: tCommon } = useTranslations('common');

  const handleGoBack = () => {
    if (window.history.length > 1) {
      navigate(-1);
    } else {
      navigate(routes.usersList);
    }
  };

  return (
    <AppBar
      position="fixed"
      sx={{
        width: { sm: `calc(100% - ${240}px)` },
        ml: { sm: `${240}px` },
        boxShadow: 'none',
        borderBottom: '1px solid #e0e0e0',
        backgroundColor: '#fff',
        color: 'text.primary',
        maxHeight: 63,
      }}
    >
      <Toolbar sx={{ display: 'flex', justifyContent: 'space-between' }}>
        <IconButton
          color="inherit"
          aria-label="open drawer"
          edge="start"
          onClick={handleDrawerToggle}
          sx={{ mr: 2, display: { sm: 'none' } }}
        >
          <MenuIcon />
        </IconButton>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <IconButton size="small" sx={{ mr: 1, color: 'text.secondary' }} onClick={handleGoBack}>
            <ArrowBackIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div">
            {tCommon(currentTitle)}
          </Typography>
        </Box>
        <LanguageToggle />
      </Toolbar>
    </AppBar>
  );
};

export default memo(Header);
