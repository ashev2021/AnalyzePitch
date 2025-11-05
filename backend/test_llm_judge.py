import json
import os
from typing import Dict, List, Optional, Tuple
from openai import OpenAI
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)

@dataclass
class EvaluationScore:
    """Structure for evaluation scores"""
    accuracy: float
    completeness: float
    relevance: float
    actionability: float
    overall: float
    reasoning: str

class EvaluationReporter:
    """Simple evaluation reporter"""
    
    def __init__(self):
        pass
    
    def generate_report(self, results: dict) -> str:
        """Generate a simple evaluation report"""
        return f"""
Evaluation Report
================
Overall Score: {results.get('overall', 0)}/10
Accuracy: {results.get('accuracy', 0)}/10
Completeness: {results.get('completeness', 0)}/10
Usefulness: {results.get('usefulness', 0)}/10

Feedback: {results.get('feedback', 'No feedback available')}
"""

class LLMJudge:
    """Simple LLM judge for evaluating investment analysis"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self.model = "openai/gpt-4-turbo"
    
    def evaluate(self, original_content: str, analysis: str) -> dict:
        """Evaluate an investment analysis"""
        
        prompt = f"""Rate this investment analysis on a scale of 1-10:

Original pitch deck content:
{original_content[:2000]}

AI analysis to evaluate:
{analysis}

Score these areas (1-10):
- Accuracy: Are the insights correct?
- Completeness: Does it cover key investment areas?
- Usefulness: Are recommendations actionable?

Return JSON format:
{{
    "accuracy": <score>,
    "completeness": <score>, 
    "usefulness": <score>,
    "overall": <average>,
    "feedback": "Brief explanation of scores"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.3
            )
            
            content = response.choices[0].message.content
            
            # Extract JSON
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end]
            
            return json.loads(content)
            
        except Exception as e:
            return {
                "accuracy": 0,
                "completeness": 0,
                "usefulness": 0,
                "overall": 0,
                "feedback": f"Error: {str(e)}"
            }

def evaluate_file(pitch_deck_path: str, analysis_path: str, api_key: str):
    """Evaluate an existing analysis file"""
    
    # Load files
    if pitch_deck_path.endswith('.pdf'):
        from app import extract_text_from_pdf
        original = extract_text_from_pdf(pitch_deck_path)
    elif pitch_deck_path.endswith('.pptx'):
        from app import extract_text_from_pptx
        original = extract_text_from_pptx(pitch_deck_path)
    else:
        raise ValueError("Only PDF and PPTX supported")
    
    with open(analysis_path, 'r') as f:
        analysis = f.read()
    
    # Evaluate
    judge = LLMJudge(api_key)
    result = judge.evaluate(original, analysis)
    
    # Save result
    eval_path = analysis_path.replace('.md', '_evaluation.json')
    with open(eval_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"Overall Score: {result['overall']}/10")
    print(f"Feedback: {result['feedback']}")
    
    return result

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 4:
        print("Usage: python llm_judge.py <pitch_deck> <analysis> <api_key>")
        sys.exit(1)
    
    try:
        evaluate_file(sys.argv[1], sys.argv[2], sys.argv[3])
    except Exception as e:
        print(f"Error: {e}")