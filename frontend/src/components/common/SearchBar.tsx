import React, { useState, useCallback } from 'react';
import { TextField, InputAdornment, IconButton, Box, debounce } from '@mui/material';
import { Search, Clear } from '@mui/icons-material';

interface SearchBarProps {
  placeholder?: string;
  value?: string;
  onChange?: (value: string) => void;
  onSearch?: (value: string) => void;
  debounceMs?: number;
  clearable?: boolean;
  fullWidth?: boolean;
  size?: 'small' | 'medium';
}

const SearchBar: React.FC<SearchBarProps> = ({
  placeholder = '検索...',
  value: controlledValue,
  onChange,
  onSearch,
  debounceMs = 300,
  clearable = true,
  fullWidth = true,
  size = 'small',
}) => {
  const [internalValue, setInternalValue] = useState('');
  const value = controlledValue !== undefined ? controlledValue : internalValue;

  const debouncedSearch = useCallback(
    debounce((searchValue: string) => {
      onSearch?.(searchValue);
    }, debounceMs),
    [onSearch, debounceMs],
  );

  const handleChange = useCallback(
    (event: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = event.target.value;
      setInternalValue(newValue);
      onChange?.(newValue);
      debouncedSearch(newValue);
    },
    [onChange, debouncedSearch],
  );

  const handleClear = useCallback(() => {
    setInternalValue('');
    onChange?.('');
    debouncedSearch('');
  }, [onChange, debouncedSearch]);

  // メインコンポーネントを分割して行数を減らす
  const SearchBarInner = () => (
    <Box sx={{ width: fullWidth ? '100%' : 'auto' }}>
      <TextField
        placeholder={placeholder}
        value={value}
        onChange={handleChange}
        size={size}
        fullWidth={fullWidth}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <Search color="action" />
            </InputAdornment>
          ),
          endAdornment:
            clearable && value ? (
              <InputAdornment position="end">
                <IconButton size="small" onClick={handleClear} edge="end" aria-label="Clear search">
                  <Clear fontSize="small" />
                </IconButton>
              </InputAdornment>
            ) : null,
        }}
      />
    </Box>
  );

  return <SearchBarInner />;
};

export default SearchBar;
