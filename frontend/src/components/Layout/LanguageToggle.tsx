import React, { useState } from 'react';
import { Box, IconButton, Menu, MenuItem, ListItemIcon, ListItemText } from '@mui/material';
import TranslateIcon from '@mui/icons-material/Translate';
import i18n from '@/i18n/config';
import nl from '@/assets/svg/nl.svg';
import us from '@/assets/svg/us.svg';

const LanguageToggle: React.FC = () => {
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const open = Boolean(anchorEl);
  const language = i18n.language;

  const handleClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLanguageChange = (newLanguage: string) => {
    i18n.changeLanguage(newLanguage);
    handleClose();
  };

  const getFlag = (language: string) => {
    if (language === 'nl') {
      return nl;
    }
    return us;
  };

  return (
    <Box>
      <IconButton
        color="inherit"
        aria-label="change language"
        onClick={handleClick}
        size="medium"
        sx={{
          ml: 1,
          border: '1px solid #e0e0e0',
          borderRadius: 1,
          padding: '4px 8px',
          '&:hover': {
            backgroundColor: 'rgba(0,0,0,0.04)',
          },
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
          <img src={getFlag(language)} width="25" alt={language} />
          <TranslateIcon fontSize="small" />
        </Box>
      </IconButton>

      <Menu
        anchorEl={anchorEl}
        open={open}
        onClose={handleClose}
        slotProps={{
          paper: {
            elevation: 2,
            sx: {
              minWidth: 180,
              borderRadius: 1,
              mt: 1.5,
              filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.1))',
            },
          },
        }}
      >
        {(['en-US', 'nl'] as const).map((lang) => (
          <MenuItem
            key={lang}
            selected={language === lang}
            onClick={() => handleLanguageChange(lang)}
            sx={{
              borderLeft: language === lang ? 3 : 0,
              borderColor: 'primary.main',
              pl: language === lang ? 1.7 : 2,
            }}
          >
            <ListItemIcon sx={{ minWidth: '32px' }}>
              <img src={getFlag(lang)} width="25" alt={language} />
            </ListItemIcon>
            <ListItemText>{lang === 'en-US' ? 'English' : 'Dutch'}</ListItemText>
          </MenuItem>
        ))}
      </Menu>
    </Box>
  );
};

export default LanguageToggle;
