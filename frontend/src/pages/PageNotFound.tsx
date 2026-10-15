import { Container, Box, Typography, Button } from '@mui/material';
import { RocketLaunch, KeyboardArrowRight } from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { keyframes } from '@mui/system';
import { routes } from '@/constants/routes';

// Create floating animation
const float = keyframes`
  0% { transform: translateY(0px); }
  50% { transform: translateY(-20px); }
  100% { transform: translateY(0px); }
`;

const PageNotFound = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          textAlign: 'center',
          py: 8,
        }}
      >
        <RocketLaunch
          sx={{
            fontSize: '8rem',
            mb: 4,
            color: 'primary.main',
            animation: `${float} 3s ease-in-out infinite`,
          }}
        />

        <Typography
          variant="h1"
          sx={{
            fontSize: '6rem',
            fontWeight: 'bold',
            mb: 2,
            background: 'linear-gradient(45deg, #FE6B8B 30%, #FF8E53 90%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
          }}
        >
          404
        </Typography>

        <Typography variant="h4" sx={{ mb: 3, fontWeight: 'medium' }}>
          Oops! Page Not Found
        </Typography>

        <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
          The page you are looking for might have been removed, had its name changed, or is
          temporarily unavailable.
        </Typography>

        <Button
          variant="contained"
          size="large"
          endIcon={<KeyboardArrowRight />}
          onClick={() => navigate(routes.home)}
          sx={{
            px: 4,
            py: 1.5,
            borderRadius: 2,
            textTransform: 'none',
            fontSize: '1.1rem',
            boxShadow: 4,
            '&:hover': {
              boxShadow: 6,
              transform: 'translateY(-2px)',
            },
            transition: 'all 0.3s ease',
          }}
        >
          Back to Home
        </Button>
      </Box>
    </Container>
  );
};

export default PageNotFound;
