import React from 'react';
import { render, screen, fireEvent, act } from '@testing-library/react';
import SearchBar from '@/components/common/SearchBar';

describe('SearchBar', () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  test('renders with default props', () => {
    render(<SearchBar />);

    const searchInput = screen.getByPlaceholderText('検索...');
    expect(searchInput).toBeInTheDocument();
    expect(searchInput).toHaveValue('');
  });

  test('renders with custom placeholder', () => {
    render(<SearchBar placeholder="Custom placeholder" />);

    const searchInput = screen.getByPlaceholderText('Custom placeholder');
    expect(searchInput).toBeInTheDocument();
  });

  test('handles controlled value', () => {
    const onChangeMock = vi.fn();
    render(<SearchBar value="test value" onChange={onChangeMock} />);

    const searchInput = screen.getByPlaceholderText('検索...');
    expect(searchInput).toHaveValue('test value');
  });

  test('calls onChange on input change', () => {
    const onChangeMock = vi.fn();
    render(<SearchBar onChange={onChangeMock} />);

    const searchInput = screen.getByPlaceholderText('検索...');
    fireEvent.change(searchInput, { target: { value: 'test' } });

    expect(onChangeMock).toHaveBeenCalledWith('test');
  });

  test('debounces onSearch callback', () => {
    const onSearchMock = vi.fn();
    render(<SearchBar onSearch={onSearchMock} debounceMs={500} />);

    const searchInput = screen.getByPlaceholderText('検索...');
    fireEvent.change(searchInput, { target: { value: 'test' } });

    expect(onSearchMock).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(500);
    });

    expect(onSearchMock).toHaveBeenCalledWith('test');
  });

  test('shows clear button when clearable and has value', () => {
    render(<SearchBar value="test" />);

    const clearButton = screen.getByRole('button', { name: /clear search/i });
    expect(clearButton).toBeInTheDocument();
  });

  test('hides clear button when clearable is false', () => {
    render(<SearchBar value="test" clearable={false} />);

    const clearButton = screen.queryByRole('button', { name: /clear search/i });
    expect(clearButton).not.toBeInTheDocument();
  });

  test('hides clear button when no value', () => {
    render(<SearchBar />);

    const clearButton = screen.queryByRole('button', { name: /clear search/i });
    expect(clearButton).not.toBeInTheDocument();
  });

  test('calls handleClear when clear button is clicked', () => {
    const onChangeMock = vi.fn();
    const onSearchMock = vi.fn();
    render(<SearchBar value="test" onChange={onChangeMock} onSearch={onSearchMock} />);

    const clearButton = screen.getByRole('button', { name: /clear search/i });
    fireEvent.click(clearButton);

    expect(onChangeMock).toHaveBeenCalledWith('');
    expect(onSearchMock).toHaveBeenCalledWith('');
  });

  test('respects fullWidth prop', () => {
    const { container } = render(<SearchBar fullWidth={false} />);

    const box = container.firstChild;
    expect(box).not.toHaveStyle({ width: '100%' });
  });

  test('respects size prop', () => {
    const { container } = render(<SearchBar size="medium" />);

    const textField = container.querySelector('input');
    expect(textField).toBeInTheDocument();
  });

  test('has proper accessibility attributes', () => {
    render(<SearchBar />);

    const searchInput = screen.getByPlaceholderText('検索...');
    expect(searchInput).toHaveAttribute('type', 'text');
    expect(searchInput).toHaveAttribute('aria-label', expect.any(String));
  });

  test('clears debounced search on unmount', () => {
    const onSearchMock = vi.fn();
    const { unmount } = render(<SearchBar onSearch={onSearchMock} />);

    const searchInput = screen.getByPlaceholderText('検索...');
    fireEvent.change(searchInput, { target: { value: 'test' } });

    unmount();

    act(() => {
      vi.advanceTimersByTime(300);
    });

    expect(onSearchMock).not.toHaveBeenCalled();
  });
});
