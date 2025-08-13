import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';

// Mock the router components
vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => vi.fn(),
    useLocation: () => ({ pathname: '/chat' }),
  };
});

describe('Layout', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders layout with children', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div data-testid="child-content">Test Content</div>
        </Layout>
      </MemoryRouter>,
    );

    const childContent = screen.getByTestId('child-content');
    expect(childContent).toBeInTheDocument();
  });

  test('renders app bar with title', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    expect(screen.getByText('チャットボット')).toBeInTheDocument();
  });

  test('renders navigation drawer with menu items', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    expect(screen.getByText('チャットボット')).toBeInTheDocument();
    expect(screen.getByText('LLM設定')).toBeInTheDocument();
    expect(screen.getByText('ナレッジ設定')).toBeInTheDocument();
  });

  test('handles drawer toggle on mobile', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    const menuButton = screen.getByLabelText('open drawer');
    expect(menuButton).toBeInTheDocument();

    fireEvent.click(menuButton);
    // Should not throw error
  });

  test('handles profile menu open and close', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    const profileButton = screen.getByLabelText('account of current user');
    fireEvent.click(profileButton);

    expect(screen.getByText('プロフィール')).toBeInTheDocument();
    expect(screen.getByText('設定')).toBeInTheDocument();
    expect(screen.getByText('ログアウト')).toBeInTheDocument();
  });

  test('has proper accessibility attributes', () => {
    render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    const menuButton = screen.getByLabelText('open drawer');
    expect(menuButton).toHaveAttribute('aria-label', 'open drawer');

    const profileButton = screen.getByLabelText('account of current user');
    expect(profileButton).toHaveAttribute('aria-label', 'account of current user');
    expect(profileButton).toHaveAttribute('aria-haspopup', 'true');
  });

  test('renders responsive layout', () => {
    const { container } = render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    const layout = container.firstChild;
    expect(layout).toHaveStyle({ display: 'flex' });
  });

  test('displays correct page title based on route', () => {
    const { rerender } = render(
      <MemoryRouter initialEntries={['/chat']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    expect(screen.getByText('チャットボット')).toBeInTheDocument();

    rerender(
      <MemoryRouter initialEntries={['/llm-config']}>
        <Layout>
          <div>Test</div>
        </Layout>
      </MemoryRouter>,
    );

    expect(screen.getByText('LLM設定')).toBeInTheDocument();
  });
});
