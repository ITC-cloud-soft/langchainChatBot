import React from 'react';
import { render, screen } from '@testing-library/react';
import PageContainer from '@/components/common/PageContainer';

describe('PageContainer', () => {
  test('renders children content', () => {
    render(
      <PageContainer>
        <div data-testid="child-content">Test Content</div>
      </PageContainer>,
    );

    const childContent = screen.getByTestId('child-content');
    expect(childContent).toBeInTheDocument();
    expect(childContent).toHaveTextContent('Test Content');
  });

  test('applies default maxWidth', () => {
    const { container } = render(<PageContainer>Test</PageContainer>);

    const containerElement = container.querySelector('.MuiContainer-root');
    expect(containerElement).toBeInTheDocument();
    expect(containerElement).toHaveClass('MuiContainer-maxWidthLg');
  });

  test('applies custom maxWidth', () => {
    const { container } = render(<PageContainer maxWidth="md">Test</PageContainer>);

    const containerElement = container.querySelector('.MuiContainer-root');
    expect(containerElement).toBeInTheDocument();
    expect(containerElement).toHaveClass('MuiContainer-maxWidthMd');
  });

  test('applies default styling', () => {
    const { container } = render(<PageContainer>Test</PageContainer>);

    const box = container.firstChild;
    expect(box).toHaveStyle({
      flexGrow: 1,
      padding: '24px',
      minHeight: '100vh',
      backgroundColor: '#f5f5f5',
    });
  });

  test('merges custom sx props', () => {
    const { container } = render(
      <PageContainer sx={{ backgroundColor: 'red', mt: 2 }}>Test</PageContainer>,
    );

    const box = container.firstChild;
    expect(box).toHaveStyle({
      flexGrow: 1,
      padding: '24px',
      minHeight: '100vh',
      backgroundColor: 'red',
      marginTop: '16px',
    });
  });

  test('handles multiple children', () => {
    render(
      <PageContainer>
        <div>Child 1</div>
        <div>Child 2</div>
        <div>Child 3</div>
      </PageContainer>,
    );

    expect(screen.getByText('Child 1')).toBeInTheDocument();
    expect(screen.getByText('Child 2')).toBeInTheDocument();
    expect(screen.getByText('Child 3')).toBeInTheDocument();
  });

  test('renders with proper structure', () => {
    const { container } = render(<PageContainer>Test</PageContainer>);

    expect(container.firstChild).toBeInTheDocument();
    expect(container.firstChild?.firstChild).toBeInTheDocument();
  });
});
