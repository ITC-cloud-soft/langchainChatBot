import React from 'react';
import {
  DataGrid,
  GridColDef,
  GridRowsProp,
  GridRowParams,
  GridRowSelectionModel,
} from '@mui/x-data-grid';
import { Box, Typography } from '@mui/material';

interface DataTableProps {
  rows: GridRowsProp;
  columns: GridColDef[];
  loading?: boolean;
  pageSize?: number;
  pageSizeOptions?: number[];
  checkboxSelection?: boolean;
  disableSelectionOnClick?: boolean;
  density?: 'compact' | 'standard' | 'comfortable';
  autoHeight?: boolean;
  height?: number | string;
  onRowClick?: (params: GridRowParams) => void;
  onSelectionModelChange?: (selectionModel: GridRowSelectionModel) => void;
  getRowClassName?: (params: GridRowParams) => string;
  sx?: React.ComponentProps<typeof Box>['sx'];
}

const DataTable: React.FC<DataTableProps> = ({
  rows,
  columns,
  loading = false,
  pageSize = 10,
  pageSizeOptions = [10, 25, 50, 100],
  checkboxSelection = false,
  disableSelectionOnClick = true,
  density = 'standard',
  autoHeight = true,
  height,
  onRowClick,
  onSelectionModelChange,
  getRowClassName,
  sx,
}) => {
  // カラムのデフォルト設定を適用
  const enhancedColumns = columns.map(column => ({
    ...column,
    sortable: column.sortable ?? true,
    filterable: column.filterable ?? true,
    disableColumnMenu: column.disableColumnMenu ?? false,
  }));

  return (
    <Box
      sx={{
        width: '100%',
        '& .MuiDataGrid-root': {
          border: '1px solid rgba(224, 224, 224, 1)',
        },
        '& .MuiDataGrid-cell': {
          borderBottom: '1px solid rgba(224, 224, 224, 1)',
        },
        '& .MuiDataGrid-columnHeaders': {
          backgroundColor: '#f5f5f5',
          borderBottom: '2px solid rgba(224, 224, 224, 1)',
        },
        '& .MuiDataGrid-columnHeaderTitle': {
          fontWeight: 600,
        },
      }}
    >
      <DataGrid
        rows={rows}
        columns={enhancedColumns}
        loading={loading}
        initialState={{
          pagination: {
            paginationModel: { pageSize },
          },
        }}
        pageSizeOptions={pageSizeOptions}
        checkboxSelection={checkboxSelection}
        disableRowSelectionOnClick={disableSelectionOnClick}
        density={density}
        autoHeight={autoHeight}
        sx={{
          height: height ? height : autoHeight ? 'auto' : '400px',
          ...sx,
        }}
        onRowClick={onRowClick}
        onRowSelectionModelChange={onSelectionModelChange}
        getRowClassName={getRowClassName}
        localeText={{
          MuiTablePagination: {
            labelRowsPerPage: '行数:',
            labelDisplayedRows: ({ from, to, count }) =>
              `${from} - ${to} / ${count !== -1 ? count : `${to}以上`}`,
          },
        }}
        slots={{
          noRowsOverlay: () => (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
                color: 'text.secondary',
              }}
            >
              <Typography>データがありません</Typography>
            </Box>
          ),
          loadingOverlay: () => (
            <Box
              sx={{
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                height: '100%',
              }}
            >
              <Typography>読み込み中...</Typography>
            </Box>
          ),
        }}
      />
    </Box>
  );
};

export default DataTable;
