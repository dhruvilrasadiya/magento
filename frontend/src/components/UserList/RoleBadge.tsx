import { Box, Typography } from '@mui/material';
import { memo } from 'react';

const ROLE_STYLES = {
  superadmin: { bg: 'rgba(255, 0, 0, 0.1)', dot: '#FF0000', text: '#FF0000' },
  admin: { bg: 'rgba(255, 165, 0, 0.1)', dot: '#FFA500', text: '#FFA500' },
  default: { bg: 'rgba(5, 150, 105, 0.1)', dot: '#059669', text: '#059669' },
};

type RoleBadgeProps = {
  role: string;
  tUsers: (key: string) => string;
};

const RoleBadge = ({ role, tUsers }: RoleBadgeProps) => {
  const styles =
    ROLE_STYLES[role === 'superadmin' ? 'superadmin' : role === 'admin' ? 'admin' : 'default'];

  return (
    <Box
      sx={{
        display: 'inline-flex',
        alignItems: 'center',
        px: 1.5,
        py: 0.5,
        borderRadius: '16px',
        bgcolor: styles.bg,
      }}
    >
      <Box sx={{ width: 8, height: 8, borderRadius: '50%', bgcolor: styles.dot, mr: 1 }} />
      <Typography variant="body2" sx={{ color: styles.text, fontWeight: 500 }}>
        {tUsers(`userManagement.role.types.${role}`)}
      </Typography>
    </Box>
  );
};

export default memo(RoleBadge);
