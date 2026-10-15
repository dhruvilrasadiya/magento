import Lottie from 'lottie-react';
import LoadingAnimation from '@/assets/lottie/loader2.json';
import { Box, Paper, Typography, keyframes } from '@mui/material';
import { memo } from 'react';
import { TFunction } from 'i18next';

type Props = {
  isMobile: boolean;
  tChat: TFunction<'common' | 'auth' | 'users' | 'chat', undefined>;
};

function Loader({ isMobile, tChat }: Props) {
  const shineAnimation = keyframes`
    0% {
      background-position: -150% 0;
    }
    100% {
      background-position: 150% 0;
    }
  `;

  return (
    <Box
      sx={{
        display: 'flex',
        justifyContent: 'flex-start',
        mb: 2,
        maxWidth: '100%',
      }}
    >
      <Paper
        elevation={0}
        sx={{
          p: 2,
          maxWidth: isMobile ? '90%' : '70%',
          bgcolor: '#FFF',
          borderRadius: '0px 10px 10px 10px',
          border: '1px solid #0000000f',
        }}
      >
        <Box sx={{ position: 'relative', paddingRight: 5 }}>
          <Typography
            sx={{
              background:
                'linear-gradient(90deg, #000 0%, #7986cb 40%, #b3c0f5 50%, #7986cb 60%, #000 100%)',
              backgroundSize: '200% auto',
              color: 'transparent',
              WebkitBackgroundClip: 'text',
              backgroundClip: 'text',
              animation: `${shineAnimation} 3s ease-in-out infinite`,
              fontWeight: 500,
              fontSize: '1.2rem',
              textShadow: '0 0 5px rgba(121,134,203,0.5)',
            }}
          >
            {tChat('response.generating')}
          </Typography>
          <Lottie
            style={{ height: 50, position: 'absolute', right: -13, top: -11 }}
            animationData={LoadingAnimation}
            loop
          />
        </Box>
      </Paper>
    </Box>
  );
}

export default memo(Loader);
