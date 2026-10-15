import { Box, Typography, Avatar } from '@mui/material';

function TessLogo() {
  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 1.5,
        cursor: 'pointer',
        transition: 'all 0.3s ease',
      }}
    >
      <Box
        className="avatar-container"
        sx={{
          background: 'linear-gradient(135deg, #1976d2 0%, #42a5f5 100%)',
          borderRadius: '50%',
          width: 48,
          height: 48,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 4px 10px rgba(25, 118, 210, 0.2)',
          transition: 'all 0.3s ease',
        }}
      >
        <Avatar
          sx={{
            bgcolor: 'transparent',
            fontSize: 26,
            fontWeight: 800,
            color: 'white',
            width: 44,
            height: 44,
            border: '2px solid rgba(255, 255, 255, 0.8)',
          }}
        >
          T
        </Avatar>
      </Box>
      <Typography
        className="logo-text"
        variant="h4"
        component="span"
        sx={{
          fontWeight: 800,
          color: '#1565c0',
          letterSpacing: 1.2,
          position: 'relative',
          textShadow: '0px 1px 1px rgba(0, 0, 0, 0.1)',
          '&::after': {
            content: '""',
            position: 'absolute',
            bottom: -4,
            left: 0,
            width: '70%',
            height: 3,
            background: 'linear-gradient(90deg, #1976d2 0%, #64b5f6 100%)',
            borderRadius: 4,
            transition: 'all 0.3s ease',
            opacity: 0.8,
          },
        }}
      >
        TESS
      </Typography>
    </Box>
  );
}

export default TessLogo;
