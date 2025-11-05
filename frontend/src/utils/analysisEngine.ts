import { ParsedDocument } from './documentParser';

export interface CompanyAnalysis {
  companyName: string;
  markdown: string;
}

// Backend API configuration
const API_BASE_URL = 'http://localhost:8000';

interface AnalysisResponse {
  success: boolean;
  analysis?: string;
  error?: string;
  metadata?: any;
}

export const analyzeDocument = async (
  document: ParsedDocument,
  openaiApiKey?: string
): Promise<CompanyAnalysis> => {
  try {
    const response = await fetch(`${API_BASE_URL}/analyze/text`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        content: document.text,
        openai_api_key: openaiApiKey
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Backend error: ${response.status} - ${errorText}`);
    }

    const result: AnalysisResponse = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Analysis failed');
    }

    const companyName = document.metadata.fileName.replace(/\.[^/.]+$/, '') || 'Company';
    
    return {
      companyName,
      markdown: result.analysis || 'No analysis available',
    };
  } catch (error) {
    console.error('Analysis error:', error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to backend. Make sure the backend server is running on http://localhost:8000');
    }
    throw error;
  }
};

// Alternative: Direct file upload to backend (bypasses frontend parsing)
export const analyzeFile = async (
  file: File,
  openaiApiKey?: string
): Promise<CompanyAnalysis> => {
  try {
    const formData = new FormData();
    formData.append('file', file);
    if (openaiApiKey) {
      formData.append('openai_api_key', openaiApiKey);
    }

    const response = await fetch(`${API_BASE_URL}/analyze/upload`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`Backend error: ${response.status} - ${errorText}`);
    }

    const result: AnalysisResponse = await response.json();
    
    if (!result.success) {
      throw new Error(result.error || 'Analysis failed');
    }

    const companyName = file.name.replace(/\.[^/.]+$/, '') || 'Company';
    
    return {
      companyName,
      markdown: result.analysis || 'No analysis available',
    };
  } catch (error) {
    console.error('File analysis error:', error);
    if (error instanceof TypeError && error.message.includes('fetch')) {
      throw new Error('Cannot connect to backend. Make sure the backend server is running on http://localhost:8000');
    }
    throw error;
  }
};
