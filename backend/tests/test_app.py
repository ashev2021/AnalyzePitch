import unittest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os
import json
import sys
from pathlib import Path

# Add parent directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (
    extract_text_from_pdf, 
    extract_text_from_pptx,
    PromptManager,
    InvestmentKnowledgeBase,
    FAISSRAGSystem,
    process_pitch_deck
)

class TestApp(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_api_key = "test-api-key"
        
    def test_investment_knowledge_base(self):
        """Test that knowledge base returns items"""
        kb_items = InvestmentKnowledgeBase.get_knowledge_items()
        
        self.assertIsInstance(kb_items, list)
        self.assertGreater(len(kb_items), 0)
        
        # Check first item structure
        first_item = kb_items[0]
        required_keys = ["id", "topic", "category", "content", "tags"]
        for key in required_keys:
            self.assertIn(key, first_item)
    
    def test_prompt_manager_with_mock_file(self):
        """Test PromptManager with mock config file"""
        mock_config = {
            "investment_analysis": {
                "system_prompt": "Test system prompt",
                "user_prompt_template": "Analyze: {content}",
                "model_config": {
                    "model": "test-model",
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            }
        }
        
        # Create temporary config file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(mock_config, f)
            temp_config_path = f.name
        
        try:
            # Test loading
            pm = PromptManager(temp_config_path)
            config = pm.get_prompt_config("investment_analysis")
            
            self.assertEqual(config["system_prompt"], "Test system prompt")
            self.assertIn("{content}", config["user_prompt_template"])
            
        finally:
            os.unlink(temp_config_path)
    
    @patch('app.fitz')
    def test_extract_text_from_pdf(self, mock_fitz):
        """Test PDF text extraction"""
        # Mock PyMuPDF
        mock_doc = Mock()
        mock_page = Mock()
        mock_page.get_text.return_value = "Test page content"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz.open.return_value = mock_doc
        
        result = extract_text_from_pdf("test.pdf")
        
        self.assertEqual(result, "Test page content")
        mock_fitz.open.assert_called_once_with("test.pdf")
        mock_doc.close.assert_called_once()
    
    @patch('app.Presentation')
    def test_extract_text_from_pptx(self, mock_presentation):
        """Test PPTX text extraction"""
        # Mock python-pptx
        mock_ppt = Mock()
        mock_slide = Mock()
        mock_shape = Mock()
        mock_shape.text = "Test slide content"
        mock_slide.shapes = [mock_shape]
        mock_ppt.slides = [mock_slide]
        mock_presentation.return_value = mock_ppt
        
        result = extract_text_from_pptx("test.pptx")
        
        self.assertEqual(result, "[Slide 1] Test slide content")
        mock_presentation.assert_called_once_with("test.pptx")
    
    @patch('app.SentenceTransformer')
    @patch('app.faiss')
    def test_faiss_rag_system_init(self, mock_faiss, mock_sentence_transformer):
        """Test RAG system initialization"""
        # Mock sentence transformer
        mock_model = Mock()
        mock_model.encode.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_sentence_transformer.return_value = mock_model
        
        # Mock FAISS
        mock_index = Mock()
        mock_faiss.IndexFlatIP.return_value = mock_index
        
        # Test initialization
        rag_system = FAISSRAGSystem()
        
        self.assertIsNotNone(rag_system.embedding_model)
        self.assertIsNotNone(rag_system.knowledge_base)
    
    @patch('app.OpenAI')
    def test_analyze_pitch_deck_with_rag_mock(self, mock_openai):
        """Test analysis function with mocked OpenAI"""
        # Create properly structured mock response
        mock_message = Mock()
        mock_message.content = "Test analysis result"
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        # Create mock prompt manager
        with patch('app.PromptManager') as mock_pm:
            mock_config = {
                "system_prompt": "Test prompt",
                "user_prompt_template": "Analyze: {content}",
                "model_config": {"model": "test-model", "max_tokens": 1000, "temperature": 0.7}
            }
            mock_pm.return_value.get_prompt_config.return_value = mock_config
            
            # Create mock RAG system
            with patch('app.FAISSRAGSystem') as mock_rag:
                mock_rag.return_value.retrieve_knowledge.return_value = [{
                    "content": "Test knowledge",
                    "topic": "test_topic", 
                    "category": "test",
                    "similarity_score": 0.8,
                    "tags": ["test"]
                }]
                
                from app import analyze_pitch_deck_with_rag
                result = analyze_pitch_deck_with_rag("test content", "test-api-key")
                
                self.assertEqual(result, "Test analysis result")
    
    def test_unsupported_file_format(self):
        """Test error handling for unsupported files"""
        with self.assertRaises(ValueError) as context:
            process_pitch_deck("test.txt", self.test_api_key)
        
        self.assertIn("Unsupported file format", str(context.exception))
    
    @patch('builtins.open', new_callable=unittest.mock.mock_open, read_data='{"investment_analysis": {"system_prompt": "test"}}')
    def test_prompt_manager_file_not_found(self, mock_file):
        """Test PromptManager with missing file"""
        mock_file.side_effect = FileNotFoundError()
        
        with self.assertRaises(FileNotFoundError):
            PromptManager("nonexistent.json")

class TestLLMJudgeIntegration(unittest.TestCase):
    """Test LLM Judge integration"""
    
    @patch('test_llm_judge.OpenAI')
    def test_llm_judge_evaluate(self, mock_openai):
        """Test LLM Judge evaluation"""
        # Import with correct path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from test_llm_judge import LLMJudge
        
        # Create properly structured mock response
        mock_message = Mock()
        mock_message.content = '''```json
{
    "accuracy": 8,
    "completeness": 7,
    "usefulness": 9,
    "overall": 8,
    "feedback": "Good analysis"
}```'''
        
        mock_choice = Mock()
        mock_choice.message = mock_message
        
        mock_response = Mock()
        mock_response.choices = [mock_choice]
        
        mock_client = Mock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        
        judge = LLMJudge("test-api-key")
        result = judge.evaluate("original content", "analysis")
        
        self.assertEqual(result["accuracy"], 8)
        self.assertEqual(result["overall"], 8)
        self.assertEqual(result["feedback"], "Good analysis")

if __name__ == '__main__':
    # Create mock prompts.json for testing
    mock_prompts = {
        "investment_analysis": {
            "system_prompt": "You are an expert investment analyst.",
            "user_prompt_template": "Please analyze this pitch deck content:\n\n{content}",
            "model_config": {
                "model": "openai/gpt-4-turbo",
                "max_tokens": 4000,
                "temperature": 0.7
            }
        }
    }
    
    # Create prompts.json in parent directory
    parent_dir = Path(__file__).parent.parent
    prompts_path = parent_dir / "prompts.json"
    
    if not prompts_path.exists():
        with open(prompts_path, "w") as f:
            json.dump(mock_prompts, f, indent=2)
        print("Created mock prompts.json for testing")
    
    unittest.main()