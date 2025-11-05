import { useState } from 'react';
import { FileUpload } from '@/components/FileUpload';
import { AnalysisResult } from '@/components/AnalysisResult';
import { analyzeFile, CompanyAnalysis } from '@/utils/analysisEngine';
import { useToast } from '@/hooks/use-toast';
import { Loader2, Sparkles } from 'lucide-react';
import { saveAs } from 'file-saver';

const Index = () => {
  const [isProcessing, setIsProcessing] = useState(false);
  const [analysis, setAnalysis] = useState<CompanyAnalysis | null>(null);
  const [apiKey, setApiKey] = useState<string>(() => {
    return localStorage.getItem('openai_api_key') || '';
  });
  const { toast } = useToast();

  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    if (value) {
      localStorage.setItem('openai_api_key', value);
    } else {
      localStorage.removeItem('openai_api_key');
    }
  };

  const handleFileSelect = async (file: File) => {
    setIsProcessing(true);
    setAnalysis(null);

    try {
      toast({
        title: 'Processing pitch deck...',
        description: 'Connecting to AI analysis engine',
      });

      // Use direct file upload to backend (no OpenAI key needed if backend has it)
      const result = await analyzeFile(file, apiKey || undefined);
      
      setAnalysis(result);
      
      toast({
        title: 'Analysis complete!',
        description: 'Your comprehensive report is ready',
      });
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred';
      
      toast({
        title: 'Analysis failed',
        description: errorMessage,
        variant: 'destructive',
      });
      
      console.error('Analysis error:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const handleDownload = () => {
    if (!analysis) return;
    
    const blob = new Blob([analysis.markdown], { type: 'text/markdown' });
    saveAs(blob, `${analysis.companyName}-analysis.md`);
    
    toast({
      title: 'Downloaded!',
      description: 'Report saved to your downloads folder',
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-b from-background to-secondary/20">
      <div className="container mx-auto px-4 py-12 max-w-4xl">
        {/* Header */}
        <header className="text-center mb-12">
          <div className="flex items-center justify-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-primary to-accent flex items-center justify-center">
              <Sparkles className="w-6 h-6 text-primary-foreground" />
            </div>
            <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent">
              Pitch Deck Analyzer
            </h1>
          </div>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Upload your pitch deck and get a comprehensive company analysis with enriched data
          </p>
        </header>

        {/* Main Content */}
        <main className="space-y-8">
          {!analysis && (
            <FileUpload onFileSelect={handleFileSelect} isProcessing={isProcessing} />
          )}

          {isProcessing && (
            <div className="flex flex-col items-center justify-center py-12 gap-4">
              <Loader2 className="w-12 h-12 text-primary animate-spin" />
              <div className="text-center">
                <p className="text-lg font-medium">Analyzing pitch deck...</p>
                <p className="text-sm text-muted-foreground">
                  Extracting information and enriching with data
                </p>
              </div>
            </div>
          )}

          {analysis && (
            <div className="space-y-4">
              <AnalysisResult
                markdown={analysis.markdown}
                onDownload={handleDownload}
                companyName={analysis.companyName}
              />
              <button
                onClick={() => setAnalysis(null)}
                className="text-sm text-muted-foreground hover:text-foreground transition-colors mx-auto block"
              >
                Analyze another pitch deck
              </button>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default Index;
