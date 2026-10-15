import {
  Box,
  Toolbar,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableRow,
  Paper,
  TablePagination,
} from '@mui/material';
import { useEffect, useState, useCallback, useMemo, cache } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  DeleteAllUsersPayload,
  DeleteDialogType,
  GetUserResponse,
  GetUsersType,
  Pagination,
  SortableKey,
  UserTokenPayload,
  Sort,
} from '@/types/types';
import { deleteAllUsers, deleteUser, getUsers } from '@/services/api';
import { enqueueSnackbar } from 'notistack';
// Icons
import { useAuth } from '@/hooks/useAuth';
import { jwtDecode } from 'jwt-decode';
import { useTranslations } from '@/i18n/hooks/useTranslations';
import DeleteDialog from '@/components/DeleteDialog/DeleteDialog';
import LoadingSkeletons from '@/components/UserList/LoadingSkeletons';
import UsersListHeader from '@/components/UserList/UsersListHeader';
import UsersTableHead from '@/components/UserList/UsersTableHead';
import UserRow from '@/components/UserList/UserRow';
import { ROWS_PER_PAGE_OPTIONS } from '@/constants/userList';
import { routes } from '@/constants/routes';

function UsersList() {
  const navigate = useNavigate();
  const { t: tUsers } = useTranslations('users');
  const { t: tCommon } = useTranslations('common');
  const { user: currentUser } = useAuth();
  const [selected, setSelected] = useState<string[]>([]);
  const [users, setUsers] = useState<GetUserResponse['users']>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [searchParams, setSearchParams] = useSearchParams();
  const [pagination, setPagination] = useState<Pagination>({
    page: Number(searchParams.get('page')) || 0,
    rowsPerPage: Number(searchParams.get('rowsPerPage')) || 5,
    total: 0,
  });
  const [sort, setSort] = useState<Sort>({
    order: 'asc',
    orderBy: 'username',
  });
  const [deleteDialog, setDeleteDialog] = useState<DeleteDialogType>({
    open: false,
    userId: null,
  });
  const [isdeleteAll, setIsDeleteAll] = useState(false);

  const jwtPayload = useMemo(
    () => (currentUser?.token ? jwtDecode<UserTokenPayload>(currentUser.token) : null),
    [currentUser?.token]
  );

  const canSelectAdmin = useMemo(() => jwtPayload?.role === 'superadmin', [jwtPayload?.role]);

  const selectableUsers = useMemo(
    () => users.filter((user) => canSelectAdmin || user.role !== 'admin'),
    [users, canSelectAdmin]
  );

  const fetchUsers = useCallback(
    cache(async () => {
      try {
        setLoading(true);
        const result = await getUsers(pagination.page, pagination.rowsPerPage);

        if (result?.status === 200) {
          setUsers(result.data.users || []);
          setPagination((prev) => ({ ...prev, total: result.data.total || 0 }));
        }
      } catch (error: any) {
        enqueueSnackbar(`${error.response?.data?.detail || tUsers('errors.gettingUsers')}`, {
          variant: 'error',
        });
        console.error('Failed to fetch users:', error);
      } finally {
        setLoading(false);
      }
    }),
    [pagination.page, pagination.rowsPerPage]
  );

  const sortedUsers = useMemo(
    () =>
      [...users].sort((a, b) => {
        if (!a[sort.orderBy] || !b[sort.orderBy]) return 0;

        const comparison = a[sort.orderBy].localeCompare(b[sort.orderBy]);
        return sort.order === 'desc' ? -comparison : comparison;
      }),
    [users, sort.order, sort.orderBy]
  );

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  const handleSelectAllClick = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (selected.length > 0 && selected.length < selectableUsers.length) {
      setSelected([]);
    } else if (event.target.checked) {
      setSelected(selectableUsers.map((user) => user.id));
    } else {
      setSelected([]);
    }
  };

  const handleRowClick = (_: React.MouseEvent<HTMLTableRowElement>, id: string) => {
    const selectedIndex = selected.indexOf(id);
    let newSelected: string[] = [];

    if (selectedIndex === -1) {
      newSelected = [...selected, id];
    } else if (selectedIndex === 0) {
      newSelected = selected.slice(1);
    } else if (selectedIndex === selected.length - 1) {
      newSelected = selected.slice(0, -1);
    } else if (selectedIndex > 0) {
      newSelected = [...selected.slice(0, selectedIndex), ...selected.slice(selectedIndex + 1)];
    }

    setSelected(newSelected);
  };

  const handlePageChange = (_: unknown, newPage: number) => {
    setPagination((prev) => ({ ...prev, page: newPage }));
    searchParams.set('page', newPage.toString());
    setSelected([]);
    setSearchParams(searchParams);
  };

  const handleRowsPerPageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const newRowsPerPage = parseInt(event.target.value, 10);
    setPagination((prev) => ({
      ...prev,
      rowsPerPage: newRowsPerPage,
      page: 0,
    }));

    searchParams.set('rowsPerPage', newRowsPerPage.toString());
    searchParams.set('page', '0');
    setSelected([]);
    setSearchParams(searchParams);
  };

  const handleRequestSort = (property: SortableKey) => {
    const isAsc = sort.orderBy === property && sort.order === 'asc';
    setSort({
      order: isAsc ? 'desc' : 'asc',
      orderBy: property,
    });
  };

  const handleCopyEmail = (email: string, event: React.MouseEvent) => {
    event.stopPropagation();
    navigator.clipboard
      .writeText(email)
      .then(() => {
        enqueueSnackbar(tCommon('clipboard.emailCopied'), { variant: 'info' });
      })
      .catch((err) => {
        console.error('Failed to copy email:', err);
        enqueueSnackbar(tCommon('clipboard.copyFailed'), { variant: 'error' });
      });
  };

  const handleEditUser = (user: GetUsersType, event: React.MouseEvent) => {
    event.stopPropagation();
    navigate(routes.userManagement + `?user=${encodeURIComponent(JSON.stringify(user))}`);
  };

  const handleDeleteClick = (id: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setDeleteDialog({ open: true, userId: id });
  };

  const handleDeleteConfirm = async () => {
    if (!deleteDialog.userId) return;

    try {
      setLoading(true);
      setDeleteDialog((prev) => ({ ...prev, open: false }));
      const result = await deleteUser(deleteDialog.userId);

      if (result?.status === 200) {
        enqueueSnackbar(tUsers('success.userDeleted'), { variant: 'success' });
        setUsers((prev) => prev.filter((user) => user.id !== deleteDialog.userId));
        setSelected((prev) => prev.filter((id) => id !== deleteDialog.userId));
        setPagination((prev) => ({ ...prev, total: prev.total - 1 }));
      }
    } catch (error: any) {
      enqueueSnackbar(`${error.response?.data?.detail || tUsers('errors.deletingUser')}`, {
        variant: 'error',
      });
      console.error('Failed to delete user:', error);
    } finally {
      setLoading(false);
      setDeleteDialog({ open: false, userId: null });
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialog({ open: false, userId: null });
  };

  const handleDeleteAllConfirm = async () => {
    try {
      setLoading(true);
      setIsDeleteAll(false);

      const payload: DeleteAllUsersPayload = {
        user_ids: selected,
      };
      const result = await deleteAllUsers(payload);

      if (result?.status === 200) {
        enqueueSnackbar(tUsers('success.userDeleted'), { variant: 'success' });
        setSelected([]);
        fetchUsers();
      }
    } catch (error: any) {
      enqueueSnackbar(`${error.response?.data?.detail || tUsers('errors.deletingUser')}`, {
        variant: 'error',
      });
      console.error('Failed to delete users:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleDeleteAllCancel = () => {
    setIsDeleteAll(false);
  };

  const isSelected = (id: string) => selected.indexOf(id) !== -1;

  return (
    <Box
      component="main"
      sx={{
        flexGrow: 1,
        p: { xs: 1.5, md: 3 },
        width: '100%',
        bgcolor: '#f5f8fa',
        minHeight: '100vh',
      }}
    >
      <Toolbar />

      <UsersListHeader
        loading={loading}
        totalUsers={pagination.total}
        selectedCount={selected.length}
        onAddUser={() => navigate(routes.userManagement)}
        onDeleteAll={() => setIsDeleteAll(true)}
        tCommon={tCommon}
        tUsers={tUsers}
      />

      <Paper sx={{ boxShadow: 'none', overflow: 'hidden' }}>
        <TableContainer style={{ minHeight: '50vh' }}>
          <Table sx={{ minWidth: 650 }}>
            <UsersTableHead
              sort={sort}
              onRequestSort={handleRequestSort}
              loading={loading}
              selectedCount={selected.length}
              selectableCount={selectableUsers.length}
              onSelectAll={handleSelectAllClick}
              tCommon={tCommon}
              tUsers={tUsers}
            />

            <TableBody>
              {loading ? (
                <LoadingSkeletons />
              ) : sortedUsers.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 6, border: 'none' }}>
                    <Typography variant="subtitle1" color="textSecondary">
                      {tUsers('userManagement.noUsersFound')}
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                sortedUsers.map((user) => (
                  <UserRow
                    key={user.id}
                    user={user}
                    isSelected={isSelected(user.id)}
                    canSelect={canSelectAdmin || user.role !== 'admin'}
                    canSelectAdmin={canSelectAdmin}
                    onRowClick={handleRowClick}
                    onCopyEmail={handleCopyEmail}
                    onEditUser={handleEditUser}
                    onDeleteClick={handleDeleteClick}
                    tCommon={tCommon}
                    tUsers={tUsers}
                  />
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>

        <TablePagination
          rowsPerPageOptions={ROWS_PER_PAGE_OPTIONS}
          component="div"
          count={pagination.total}
          rowsPerPage={pagination.rowsPerPage}
          page={pagination.page}
          labelRowsPerPage={tUsers('userManagement.rowsPerPage')}
          onPageChange={handlePageChange}
          onRowsPerPageChange={handleRowsPerPageChange}
        />
      </Paper>

      <DeleteDialog
        deleteDialogOpen={deleteDialog.open || isdeleteAll}
        cancelDelete={isdeleteAll ? handleDeleteAllCancel : handleDeleteCancel}
        confirmDelete={isdeleteAll ? handleDeleteAllConfirm : handleDeleteConfirm}
        title={
          isdeleteAll ? tUsers('deleteAllConfirmation.title') : tUsers('deleteConfirmation.title')
        }
        description={
          isdeleteAll
            ? tUsers('deleteAllConfirmation.message')
            : tUsers('deleteConfirmation.message')
        }
      />
    </Box>
  );
}

export default UsersList;
