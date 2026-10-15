import { TableRow, TableCell, Skeleton, Box } from '@mui/material';

const LoadingSkeletons = () => {
  return Array.from(new Array(5)).map((_, index) => (
    <TableRow key={`skeleton-${index}`}>
      <TableCell padding="checkbox">
        <Skeleton variant="rectangular" width={24} height={24} />
      </TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', alignItems: 'center' }}>
          <Skeleton variant="circular" width={40} height={40} sx={{ mr: 2 }} />
          <Skeleton variant="text" width={120} />
        </Box>
      </TableCell>
      <TableCell>
        <Skeleton variant="text" width={180} />
      </TableCell>
      <TableCell>
        <Skeleton variant="text" width={80} />
      </TableCell>
      <TableCell>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Skeleton variant="circular" width={32} height={32} />
          <Skeleton variant="circular" width={32} height={32} />
        </Box>
      </TableCell>
    </TableRow>
  ));
};

export default LoadingSkeletons;
