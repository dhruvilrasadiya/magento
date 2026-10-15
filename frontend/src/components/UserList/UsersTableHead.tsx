import { TableCell, TableHead, TableRow, TableSortLabel, Checkbox } from '@mui/material';
import RequirePermission from '@/components/RequirePermission/RequirePermission';
import { Sort, SortableKey } from '@/types/types';
import { memo } from 'react';

type UsersTableHeadProps = {
  sort: Sort;
  onRequestSort: (property: SortableKey) => void;
  loading: boolean;
  selectedCount: number;
  selectableCount: number;
  onSelectAll: (event: React.ChangeEvent<HTMLInputElement>) => void;
  tCommon: (key: string) => string;
  tUsers: (key: string) => string;
};

const UsersTableHead = ({
  sort,
  onRequestSort,
  loading,
  selectedCount,
  selectableCount,
  onSelectAll,
  tCommon,
  tUsers,
}: UsersTableHeadProps) => (
  <TableHead>
    <TableRow>
      <RequirePermission permission="edit:all">
        <TableCell padding="checkbox">
          <Checkbox
            indeterminate={selectedCount > 0 && selectedCount < selectableCount}
            checked={selectableCount > 0 && selectedCount === selectableCount}
            onChange={onSelectAll}
            disabled={loading}
          />
        </TableCell>
      </RequirePermission>

      {(['username', 'email', 'role'] as const).map((field) => (
        <TableCell key={field}>
          <TableSortLabel
            active={sort.orderBy === field}
            direction={sort.orderBy === field ? sort.order : 'asc'}
            onClick={() => onRequestSort(field)}
            disabled={loading}
          >
            {field === 'username'
              ? tCommon('form.name')
              : field === 'email'
              ? tCommon('form.email')
              : tUsers('userManagement.role.label')}
          </TableSortLabel>
        </TableCell>
      ))}

      <TableCell>
        <RequirePermission permission="edit:supervisor">{tCommon('ui.options')}</RequirePermission>
      </TableCell>
    </TableRow>
  </TableHead>
);

export default memo(UsersTableHead);
