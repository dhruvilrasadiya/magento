import {
  Avatar,
  Box,
  Checkbox,
  IconButton,
  TableCell,
  TableRow,
  Tooltip,
  Typography,
} from '@mui/material';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import RequirePermission from '@/components/RequirePermission/RequirePermission';
import RoleBadge from './RoleBadge';
import { GetUsersType } from '@/types/types';
import { memo, MouseEvent } from 'react';

type UserRowProps = {
  user: GetUsersType;
  isSelected: boolean;
  canSelect: boolean;
  canSelectAdmin: boolean;
  onRowClick: (_: MouseEvent<HTMLTableRowElement, globalThis.MouseEvent>, id: string) => void;
  onCopyEmail: (email: string, event: React.MouseEvent) => void;
  onEditUser: (user: GetUsersType, event: React.MouseEvent) => void;
  onDeleteClick: (id: string, event: React.MouseEvent) => void;
  tCommon: (key: string) => string;
  tUsers: (key: string) => string;
};

const UserRow = ({
  user,
  isSelected,
  canSelect,
  canSelectAdmin,
  onRowClick,
  onCopyEmail,
  onEditUser,
  onDeleteClick,
  tCommon,
  tUsers,
}: UserRowProps) => (
  <TableRow
    hover
    onClick={canSelect ? (event) => onRowClick(event, user.id) : undefined}
    role="checkbox"
    aria-checked={isSelected}
    tabIndex={-1}
    key={user.id}
    selected={isSelected}
    sx={{
      '&.Mui-selected, &.Mui-selected:hover': { bgcolor: 'rgba(25, 118, 210, 0.08)' },
      transition: 'background-color 0.2s',
      cursor: canSelect ? 'pointer' : 'default',
    }}
  >
    <RequirePermission permission="edit:all">
      <TableCell padding="checkbox">
        <Checkbox checked={isSelected} disabled={!canSelect} />
      </TableCell>
    </RequirePermission>

    <TableCell component="th" scope="row">
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Avatar sx={{ mr: 2, bgcolor: '#1976d2', boxShadow: '0 2px 5px rgba(0,0,0,0.1)' }}>
          {user.username.charAt(0).toUpperCase()}
        </Avatar>
        <Typography variant="body1" fontWeight={500}>
          {user.username}
        </Typography>
      </Box>
    </TableCell>

    <TableCell>
      <Box sx={{ display: 'flex', alignItems: 'center' }}>
        <Typography variant="body2" sx={{ mr: 1 }}>
          {user.email}
        </Typography>
        <Tooltip title={tCommon('clipboard.copyEmail')} arrow disableInteractive>
          <IconButton
            size="small"
            onClick={(e) => onCopyEmail(user.email, e)}
            sx={{ color: '#757575', '&:hover': { color: '#1976d2' } }}
          >
            <ContentCopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>
    </TableCell>

    <TableCell>
      <RoleBadge role={user.role} tUsers={tUsers} />
    </TableCell>

    <TableCell>
      <RequirePermission
        permission="edit:supervisor"
        condition={() => canSelectAdmin || user.role !== 'admin'}
      >
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title={tUsers('actions.editUser')} arrow disableInteractive>
            <span>
              <IconButton
                sx={{ bgcolor: '#e8f5e9', color: '#4caf50', '&:hover': { bgcolor: '#c8e6c9' } }}
                size="small"
                onClick={(e) => onEditUser(user, e)}
                disabled={isSelected}
              >
                <EditIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
          <Tooltip title={tUsers('actions.deleteUser')} arrow disableInteractive>
            <span>
              <IconButton
                sx={{ bgcolor: '#ffebee', color: '#f44336', '&:hover': { bgcolor: '#ffcdd2' } }}
                size="small"
                onClick={(e) => onDeleteClick(user.id, e)}
                disabled={isSelected}
              >
                <DeleteIcon fontSize="small" />
              </IconButton>
            </span>
          </Tooltip>
        </Box>
      </RequirePermission>
    </TableCell>
  </TableRow>
);

export default memo(UserRow);
