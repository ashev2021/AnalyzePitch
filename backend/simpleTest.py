"""
Tests for backend/app.py
"""
import pytest
import json
import tempfile
import os
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Change this import - remove 'backend.' prefix since we're already in the backend directory
from app import (
    PromptManager,
    InvestmentKnowledgeBase,
    FAISSRAGSystem,
    extract_text_from_pdf,
    extract_text_from_pptx,
    analyze_pitch_deck_with_rag,
    process_pitch_deck
)


class TestPromptManager:
    def test_load_prompts_success(self, tmp_path):
        """Test successful prompt loading"""
        config_file = tmp_path / "test_prompts.json"
        config_data = {
            "investment_analysis": {
                "system_prompt": "Test system prompt",
                "user_prompt_template": "Test user prompt: {content}",
                "model_config": {
                    "model": "gpt-3.5-turbo",
                    "max_tokens": 1000,
                    "temperature": 0.1
                }
            }
        }
        config_file.write_text(json.dumps(config_data))
        
        pm = PromptManager(str(config_file))
        assert pm.prompts == config_data
    
    def test_load_prompts_file_not_found(self):
        """Test FileNotFoundError when config file doesn't exist"""
        with pytest.raises(FileNotFoundError):
            PromptManager("nonexistent_file.json")
    
    def test_load_prompts_invalid_json(self, tmp_path):
        """Test ValueError for invalid JSON"""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("invalid json content")
        
        with pytest.raises(ValueError):
            PromptManager(str(config_file))
    
    def test_get_prompt_config_success(self, tmp_path):
        """Test successful prompt config retrieval"""
        config_file = tmp_path / "test_prompts.json"
        config_data = {
            "investment_analysis": {"system_prompt": "Test prompt"}
        }
        config_file.write_text(json.dumps(config_data))
        
        pm = PromptManager(str(config_file))
        config = pm.get_prompt_config("investment_analysis")
        assert config["system_prompt"] == "Test prompt"
    
    def test_get_prompt_config_not_found(self, tmp_path):
        """Test ValueError when prompt type not found"""
        config_file = tmp_path / "test_prompts.json"
        config_file.write_text('{"other_type": {}}')
        
        pm = PromptManager(str(config_file))
        with pytest.raises(ValueError):
            pm.get_prompt_config("investment_analysis")


class TestInvestmentKnowledgeBase:
    def test_get_knowledge_items(self):
        """Test knowledge base returns expected structure"""
        items = InvestmentKnowledgeBase.get_knowledge_items()
        
        assert isinstance(items, list)
        assert len(items) == 10
        
        # Check first item structure
        first_item = items[0]
        assert "id" in first_item
        assert "topic" in first_item
        assert "category" in first_item
        assert "content" in first_item
        assert "tags" in first_item
        assert isinstance(first_item["tags"], list)


class TestFAISSRAGSystem:
    @patch('app.SentenceTransformer')  # Remove 'backend.' prefix
    @patch('app.faiss')  # Remove 'backend.' prefix
    def test_init_with_mocks(self, mock_faiss, mock_sentence_transformer):
        """Test FAISSRAGSystem initialization"""
        mock_model = Mock()
        mock_sentence_transformer.return_value = mock_model
        
        with patch.object(FAISSRAGSystem, '_build_or_load_index'):
            rag_system = FAISSRAGSystem()
            
            assert rag_system.embedding_model == mock_model
            assert len(rag_system.knowledge_base) == 10
    
    @patch('app.SentenceTransformer')  # Remove 'backend.' prefix
    @patch('app.faiss')  # Remove 'backend.' prefix
    def test_retrieve_knowledge(self, mock_faiss, mock_sentence_transformer):
        """Test knowledge retrieval"""
        # Mock sentence transformer
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
        mock_sentence_transformer.return_value = mock_model
        
        # Mock FAISS index
        mock_index = Mock()
        mock_index.search.return_value = ([[0.8, 0.6]], [[0, 1]])
        mock_faiss.normalize_L2 = Mock()
        
        with patch.object(FAISSRAGSystem, '_build_or_load_index'):
            rag_system = FAISSRAGSystem()
            rag_system.index = mock_index
            
            results = rag_system.retrieve_knowledge("test query", top_k=2, similarity_threshold=0.5)
            
            assert len(results) == 2
            assert results[0]["similarity_score"] == 0.8
            assert "content" in results[0]
            assert "topic" in results[0]


class TestTextExtraction:
    @patch('app.fitz')  # Remove 'backend.' prefix
    def test_extract_text_from_pdf(self, mock_fitz):
        """Test PDF text extraction"""
        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Page content"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_doc.close = Mock()
        mock_fitz.open.return_value = mock_doc
        
        result = extract_text_from_pdf("test.pdf")
        
        assert result == "Page content"
        mock_fitz.open.assert_called_once_with("test.pdf")
        mock_doc.close.assert_called_once()
    
    @patch('app.Presentation')  # Remove 'backend.' prefix
    def test_extract_text_from_pptx(self, mock_presentation):
        """Test PPTX text extraction"""
        # Mock python-pptx
        mock_shape = Mock()
        mock_shape.text = "Slide text"
        mock_slide = Mock()
        mock_slide.shapes = [mock_shape]
        
        mock_ppt = Mock()
        mock_ppt.slides = [mock_slide]
        mock_presentation.return_value = mock_ppt
        
        result = extract_text_from_pptx("test.pptx")
        
        assert result == "[Slide 1] Slide text"
        mock_presentation.assert_called_once_with("test.pptx")


class TestAnalyzePitchDeck:
    @patch('app.OpenAI')  # Remove 'backend.' prefix
    @patch('app.FAISSRAGSystem')  # Remove 'backend.' prefix
    @patch('app.PromptManager')  # Remove 'backend.' prefix
    def test_analyze_pitch_deck_with_rag(self, mock_prompt_manager, mock_rag_system, mock_openai):
        """Test pitch deck analysis with RAG"""
        # Mock PromptManager
        mock_pm = Mock()
        mock_pm.get_prompt_config.return_value = {
            "system_prompt": "Test system prompt",
            "user_prompt_template": "Analyze: {content}",
            "model_config": {
                "model": "gpt-3.5-turbo",
                "max_tokens": 1000,
                "temperature": 0.1
            }
        }
        mock_prompt_manager.return_value = mock_pm
        
        # Mock RAG system
        mock_rag = Mock()
        mock_rag.retrieve_knowledge.return_value = [
            {
                "content": "Test knowledge",
                "topic": "test_topic",
                "category": "test_category",
                "similarity_score": 0.8,
                "tags": ["test"]
            }
        ]
        mock_rag_system.return_value = mock_rag
        
        # Mock OpenAI
        mock_client = Mock()
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test analysis result"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        result = analyze_pitch_deck_with_rag("test content", "test-api-key")
        
        assert result == "Test analysis result"
        mock_rag.retrieve_knowledge.assert_called_once_with("test content", top_k=7)


class TestProcessPitchDeck:
    @patch('app.analyze_pitch_deck_with_rag')  # Remove 'backend.' prefix
    @patch('app.FAISSRAGSystem')  # Remove 'backend.' prefix
    @patch('app.PromptManager')  # Remove 'backend.' prefix
    @patch('app.extract_text_from_pdf')  # Remove 'backend.' prefix
    @patch('builtins.open', create=True)
    def test_process_pitch_deck_pdf(self, mock_open, mock_extract_pdf, mock_prompt_manager, 
                                   mock_rag_system, mock_analyze):
        """Test processing PDF pitch deck"""
        mock_extract_pdf.return_value = "Extracted PDF text"
        mock_analyze.return_value = "Analysis result"
        mock_file = Mock()
        mock_open.return_value.__enter__.return_value = mock_file
        
        with patch('builtins.print'):
            process_pitch_deck("test.pdf", "test-api-key")
        
        mock_extract_pdf.assert_called_once_with("test.pdf")
        mock_analyze.assert_called_once()
        mock_file.write.assert_called()
    
    @patch('app.extract_text_from_pptx')  # Remove 'backend.' prefix
    def test_process_pitch_deck_pptx(self, mock_extract_pptx):
        """Test processing PPTX pitch deck"""
        mock_extract_pptx.return_value = "Extracted PPTX text"
        
        with patch('app.analyze_pitch_deck_with_rag') as mock_analyze, \
             patch('app.FAISSRAGSystem'), \
             patch('app.PromptManager'), \
             patch('builtins.open', create=True), \
             patch('builtins.print'):
            
            mock_analyze.return_value = "Analysis result"
            process_pitch_deck("test.pptx", "test-api-key")
            
        mock_extract_pptx.assert_called_once_with("test.pptx")
    
    def test_process_pitch_deck_unsupported_format(self):
        """Test error handling for unsupported file format"""
        with pytest.raises(ValueError, match="Unsupported file format"):
            process_pitch_deck("test.txt", "test-api-key")
    
    @patch('app.extract_text_from_pdf')  # Remove 'backend.' prefix
    @patch('app.PromptManager')  # Remove 'backend.' prefix
    def test_process_pitch_deck_prompt_manager_error(self, mock_prompt_manager, mock_extract_pdf):
        """Test handling PromptManager errors"""
        mock_extract_pdf.return_value = "Extracted text"
        mock_prompt_manager.side_effect = FileNotFoundError("Config not found")
        
        with patch('builtins.print') as mock_print:
            process_pitch_deck("test.pdf", "test-api-key")
            
        # Check that error was printed
        mock_print.assert_any_call("Error during analysis: Config not found")


# Fixtures for common test data
@pytest.fixture
def sample_knowledge_item():
    return {
        "id": 0,
        "topic": "test_topic",
        "category": "test_category",
        "content": "Test content for investment knowledge",
        "tags": ["test", "knowledge"]
    }

@pytest.fixture
def mock_openai_response():
    mock_response = Mock()
    mock_response.choices = [Mock()]
    mock_response.choices[0].message.content = "Mock analysis result"
    return mock_response