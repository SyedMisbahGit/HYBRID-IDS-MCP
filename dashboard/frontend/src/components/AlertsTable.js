import React from 'react';
import { 
  Table, 
  TableBody, 
  TableCell, 
  TableContainer, 
  TableHead, 
  TableRow, 
  Paper, 
  Chip, 
  Box, 
  Typography, 
  Tooltip, 
  IconButton, 
  TablePagination, 
  TableSortLabel
} from '@mui/material';
import { visuallyHidden } from '@mui/utils';
import { styled } from '@mui/material/styles';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import InfoIcon from '@mui/icons-material/Info';
import MoreVertIcon from '@mui/icons-material/MoreVert';

const StyledTableRow = styled(TableRow)(({ theme }) => ({
  '&:nth-of-type(odd)': {
    backgroundColor: theme.palette.action.hover,
  },
  '&:last-child td, &:last-child th': {
    border: 0,
  },
  '&:hover': {
    backgroundColor: theme.palette.action.selected,
    '& .actions': {
      opacity: 1,
    },
  },
}));

const severityIcons = {
  critical: <ErrorIcon color="error" fontSize="small" />,
  high: <ErrorIcon color="error" fontSize="small" />,
  medium: <WarningIcon color="warning" fontSize="small" />,
  low: <InfoIcon color="info" fontSize="small" />,
};

const severityColors = {
  critical: 'error',
  high: 'error',
  medium: 'warning',
  low: 'info',
};

const formatDate = (dateString) => {
  try {
    const date = new Date(dateString);
    return date.toLocaleString();
  } catch (e) {
    return 'N/A';
  }
};

const getCellValue = (row, column) => {
  // Handle nested properties
  const value = column.id.split('.').reduce((obj, key) => 
    (obj && obj[key] !== undefined) ? obj[key] : '', row);
  
  // Format based on column type or value
  if (column.format) {
    return column.format(value);
  }
  
  if (column.id === 'timestamp') {
    return formatDate(value);
  }
  
  if (column.id === 'severity') {
    return (
      <Chip
        icon={severityIcons[value.toLowerCase()] || <InfoIcon />}
        label={value}
        color={severityColors[value.toLowerCase()] || 'default'}
        size="small"
        variant="outlined"
      />
    );
  }
  
  return value || '-';
};

const AlertsTable = ({ 
  alerts = [], 
  columns = [
    { id: 'timestamp', label: 'Timestamp', minWidth: 170 },
    { id: 'type', label: 'Type', minWidth: 120 },
    { id: 'severity', label: 'Severity', minWidth: 100 },
    { id: 'description', label: 'Description', minWidth: 200 },
  ],
  pageSize = 10,
  showPagination = true,
  onRowClick,
  emptyMessage = 'No alerts to display'
}) => {
  const [page, setPage] = React.useState(0);
  const [rowsPerPage, setRowsPerPage] = React.useState(pageSize);
  const [order, setOrder] = React.useState('desc');
  const [orderBy, setOrderBy] = React.useState('timestamp');

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(+event.target.value);
    setPage(0);
  };

  const handleRequestSort = (property) => {
    const isAsc = orderBy === property && order === 'asc';
    setOrder(isAsc ? 'desc' : 'asc');
    setOrderBy(property);
  };

  const sortedAlerts = React.useMemo(() => {
    return [...alerts].sort((a, b) => {
      if (orderBy === 'timestamp') {
        return order === 'asc' 
          ? new Date(a[orderBy]) - new Date(b[orderBy])
          : new Date(b[orderBy]) - new Date(a[orderBy]);
      }
      if (a[orderBy] < b[orderBy]) {
        return order === 'asc' ? -1 : 1;
      }
      if (a[orderBy] > b[orderBy]) {
        return order === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [alerts, order, orderBy]);

  const paginatedAlerts = showPagination
    ? sortedAlerts.slice(page * rowsPerPage, page * rowsPerPage + rowsPerPage)
    : sortedAlerts;
  if (!alerts || alerts.length === 0) {
    return (
      <Box
        display="flex"
        flexDirection="column"
        alignItems="center"
        justifyContent="center"
        minHeight={200}
        p={3}
        textAlign="center"
      >
        <InfoIcon color="action" fontSize="large" />
        <Typography variant="body1" color="textSecondary" sx={{ mt: 1 }}>
          No security alerts detected
        </Typography>
        <Typography variant="body2" color="textSecondary">
        </Typography>
      </Box>
    );
  }

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden' }}>
      <TableContainer sx={{ maxHeight: 600 }}>
        <Table stickyHeader aria-label="alerts table" size="small">
          <TableHead>
            <TableRow>
              {columns.map((column) => (
                <TableCell
                  key={column.id}
                  align={column.align || 'left'}
                  style={{ minWidth: column.minWidth }}
                  sortDirection={orderBy === column.id ? order : false}
                >
                  <TableSortLabel
                    active={orderBy === column.id}
                    direction={orderBy === column.id ? order : 'asc'}
                    onClick={() => handleRequestSort(column.id)}
                  >
                    {column.label}
                    {orderBy === column.id ? (
                      <Box component="span" sx={visuallyHidden}>
                        {order === 'desc' ? 'sorted descending' : 'sorted ascending'}
                      </Box>
                    ) : null}
                  </TableSortLabel>
                </TableCell>
              ))}
              <TableCell align="right" style={{ width: 50 }}>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {paginatedAlerts.map((alert) => (
              <StyledTableRow 
                hover 
                key={alert.id}
                onClick={() => onRowClick && onRowClick(alert)}
                sx={{ cursor: onRowClick ? 'pointer' : 'default' }}
              >
                {columns.map((column) => (
                  <TableCell 
                    key={column.id}
                    align={column.align || 'left'}
                    sx={{
                      whiteSpace: 'nowrap',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      maxWidth: column.maxWidth || 'none',
                    }}
                  >
                    {getCellValue(alert, column)}
                  </TableCell>
                ))}
                <TableCell align="right" className="actions" sx={{ opacity: 0, transition: 'opacity 0.2s' }}>
                  <Tooltip title="More actions">
                    <IconButton size="small">
                      <MoreVertIcon fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </StyledTableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {showPagination && (
        <TablePagination
          rowsPerPageOptions={[5, 10, 25, 100]}
          component="div"
          count={alerts.length}
          rowsPerPage={rowsPerPage}
          page={page}
          onPageChange={handleChangePage}
          onRowsPerPageChange={handleChangeRowsPerPage}
        />
      )}
    </Paper>
  );
};

export default AlertsTable;
