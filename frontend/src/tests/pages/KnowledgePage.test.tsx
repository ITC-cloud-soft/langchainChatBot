import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import KnowledgePage from '@/pages/KnowledgePage';

// Mock the API
vi.mock('@/services/api', () => ({
  knowledgeApi: {
    getCollectionInfo: vi.fn().mockResolvedValue({
      success: true,
      data: {
        name: 'test-collection',
        document_count: 5,
        vector_count: 100,
      },
    }),
    listDocuments: vi.fn().mockResolvedValue({
      success: true,
      data: {
        documents: [
          { id: '1', content: 'Test doc 1', metadata: { source: 'test1' } },
          { id: '2', content: 'Test doc 2', metadata: { source: 'test2' } },
        ],
        total: 2,
      },
    }),
    uploadDocument: vi.fn().mockResolvedValue({
      success: true,
      data: { message: 'Document uploaded' },
    }),
    deleteDocument: vi.fn().mockResolvedValue({
      success: true,
      data: { message: 'Document deleted' },
    }),
    searchKnowledge: vi.fn().mockResolvedValue({
      success: true,
      data: {
        results: [
          { content: 'Search result 1', score: 0.9 },
          { content: 'Search result 2', score: 0.8 },
        ],
        total: 2,
      },
    }),
  },
}));

vi.mock('notistack', () => ({
  useSnackbar: () => ({
    enqueueSnackbar: vi.fn(),
  }),
}));

vi.mock('react-dropzone', () => ({
  useDropzone: () => ({
    getRootProps: () => ({}),
    getInputProps: () => ({}),
    isDragActive: false,
  }),
}));

describe('KnowledgePage', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  test('renders knowledge management page', async () => {
    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/ナレッジ設定/i)).toBeInTheDocument();
    });
  });

  test('displays collection information', async () => {
    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText(/test-collection/i)).toBeInTheDocument();
      expect(screen.getByText(/5/i)).toBeInTheDocument();
      expect(screen.getByText(/100/i)).toBeInTheDocument();
    });
  });

  test('displays documents list', async () => {
    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      expect(screen.getByText('Test doc 1')).toBeInTheDocument();
      expect(screen.getByText('Test doc 2')).toBeInTheDocument();
    });
  });

  test('handles search functionality', async () => {
    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/検索/i);
      fireEvent.change(searchInput, { target: { value: 'test query' } });

      const searchButton = screen.getByRole('button', { name: /検索/i });
      fireEvent.click(searchButton);
    });

    await waitFor(() => {
      expect(screen.getByText('Search result 1')).toBeInTheDocument();
      expect(screen.getByText('Search result 2')).toBeInTheDocument();
    });
  });

  test('handles document deletion', async () => {
    const { enqueueSnackbar } = vi.mocked(require('notistack')).useSnackbar();

    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const deleteButton = screen.getAllByRole('button', { name: /削除/i })[0];
      fireEvent.click(deleteButton);
    });

    await waitFor(() => {
      expect(enqueueSnackbar).toHaveBeenCalledWith(
        expect.stringContaining('ドキュメントを削除しました'),
        expect.objectContaining({ variant: 'success' }),
      );
    });
  });

  test('handles file upload', async () => {
    const { enqueueSnackbar } = vi.mocked(require('notistack')).useSnackbar();

    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const uploadButton = screen.getByRole('button', { name: /アップロード/i });
      fireEvent.click(uploadButton);
    });

    await waitFor(() => {
      expect(enqueueSnackbar).toHaveBeenCalledWith(
        expect.stringContaining('ドキュメントをアップロードしました'),
        expect.objectContaining({ variant: 'success' }),
      );
    });
  });

  test('displays loading states', async () => {
    vi.mock('@/services/api', () => ({
      knowledgeApi: {
        getCollectionInfo: vi
          .fn()
          .mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000))),
        listDocuments: vi.fn().mockResolvedValue({ success: true }),
        uploadDocument: vi.fn().mockResolvedValue({ success: true }),
        deleteDocument: vi.fn().mockResolvedValue({ success: true }),
        searchKnowledge: vi.fn().mockResolvedValue({ success: true }),
      },
    }));

    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    expect(screen.getByRole('progressbar')).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.queryByRole('progressbar')).not.toBeInTheDocument();
    }, 1500);
  });

  test('has proper accessibility attributes', async () => {
    render(
      <MemoryRouter>
        <KnowledgePage />
      </MemoryRouter>,
    );

    await waitFor(() => {
      const searchInput = screen.getByPlaceholderText(/検索/i);
      expect(searchInput).toHaveAttribute('type', 'text');
      expect(searchInput).toHaveAttribute('aria-label', expect.any(String));

      const deleteButtons = screen.getAllByRole('button', { name: /削除/i });
      deleteButtons.forEach(button => {
        expect(button).toHaveAttribute('aria-label', expect.any(String));
      });
    });
  });
});
