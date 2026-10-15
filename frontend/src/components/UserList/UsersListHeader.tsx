import { Box, Button, Skeleton, Typography } from '@mui/material';
import AddIcon from '@mui/icons-material/Add';
import Delete from '@mui/icons-material/Delete';
import RequirePermission from '@/components/RequirePermission/RequirePermission';
import { memo } from 'react';

type UsersListHeaderProps = {
  loading: boolean;
  totalUsers: number;
  selectedCount: number;
  onAddUser: () => void;
  onDeleteAll: () => void;
  tCommon: (key: string) => string;
  tUsers: (key: string) => string;
};

const UsersListHeader = ({
  loading,
  totalUsers,
  selectedCount,
  onAddUser,
  onDeleteAll,
  tCommon,
  tUsers,
}: UsersListHeaderProps) => (
  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
    <Typography variant="body1" color="textSecondary">
      {loading ? <Skeleton width={100} /> : `${totalUsers} ${tCommon('ui.results')}`}
    </Typography>

    <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
      <RequirePermission permission="create:user">
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          sx={{
            bgcolor: '#0d47a1',
            '&:hover': { bgcolor: '#002171' },
            transition: 'background-color 0.3s',
            boxShadow: 2,
          }}
          onClick={onAddUser}
          disabled={loading}
        >
          {tUsers('actions.addNewUser')}
        </Button>
      </RequirePermission>
      {selectedCount > 1 && (
        <RequirePermission permission="delete:all">
          <Button
            variant="outlined"
            color="error"
            startIcon={<Delete />}
            onClick={onDeleteAll}
            disabled={loading}
          >
            {tUsers('actions.deleteAll')}
          </Button>
        </RequirePermission>
      )}
    </Box>
  </Box>
);

export default memo(UsersListHeader);
