import numpy as np
from unittest.mock import Mock, patch

from app import FAISSRAGSystem


@patch('app.SentenceTransformer')
@patch('app.faiss')
def test_faiss_rag_system_init(self, mock_faiss, mock_sentence_transformer):
    """Test RAG system initialization"""
    # Mock sentence transformer
    mock_model = Mock()
    # Return numpy array instead of list
    mock_model.encode.return_value = np.array([[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]])
    mock_sentence_transformer.return_value = mock_model

    # Mock FAISS
    mock_index = Mock()
    mock_index.ntotal = 0  # Mock index size
    mock_faiss.IndexFlatIP.return_value = mock_index
    mock_faiss.normalize_L2 = Mock()  # Mock normalize function

    # Test initialization
    rag_system = FAISSRAGSystem()
    
    # Assertions
    assert rag_system is not None
    assert mock_sentence_transformer.called
    assert mock_faiss.IndexFlatIP.called