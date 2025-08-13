import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import ErrorAlert from '@/components/common/ErrorAlert';

describe('ErrorAlert', () => {
  test('renders with default props', () => {
    render(<ErrorAlert message="Test error message" />);

    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveTextContent('Test error message');
    expect(alert).toHaveTextContent('エラー');
  });

  test('renders with custom title', () => {
    render(<ErrorAlert title="Custom Title" message="Test message" />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('Custom Title');
    expect(alert).toHaveTextContent('Test message');
  });

  test('renders with different severity levels', () => {
    const severities = ['error', 'warning', 'info', 'success'] as const;

    severities.forEach(severity => {
      const { container, rerender } = render(
        <ErrorAlert message="Test message" severity={severity} />,
      );

      const alert = screen.getByRole('alert');
      expect(alert).toBeInTheDocument();

      rerender(<ErrorAlert message="Test message" severity={severity} />);
    });
  });

  test('calls onClose when close button is clicked', () => {
    const onCloseMock = vi.fn();
    render(<ErrorAlert message="Test message" onClose={onCloseMock} />);

    const closeButton = screen.getByRole('button', { name: /close/i });
    fireEvent.click(closeButton);

    expect(onCloseMock).toHaveBeenCalledTimes(1);
  });

  test('does not show close button when onClose is not provided', () => {
    render(<ErrorAlert message="Test message" />);

    const closeButton = screen.queryByRole('button', { name: /close/i });
    expect(closeButton).not.toBeInTheDocument();
  });

  test('has correct accessibility attributes', () => {
    render(<ErrorAlert message="Test message" />);

    const alert = screen.getByRole('alert');
    expect(alert).toHaveAttribute('role', 'alert');
  });

  test('renders with proper styling', () => {
    const { container } = render(<ErrorAlert message="Test message" />);

    const box = container.firstChild;
    expect(box).toHaveStyle({ marginBottom: '16px' });
  });
});
