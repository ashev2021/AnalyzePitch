import { Download, FileText, CheckCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';

interface AnalysisResultProps {
  markdown: string;
  onDownload: () => void;
  companyName?: string;
}

export const AnalysisResult = ({ markdown, onDownload, companyName }: AnalysisResultProps) => {
  const sections = markdown.split('\n## ').filter(Boolean);
  
  return (
    <Card className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center">
            <CheckCircle className="w-6 h-6 text-primary" />
          </div>
          <div>
            <h3 className="text-xl font-semibold">Analysis Complete</h3>
            {companyName && (
              <p className="text-sm text-muted-foreground">{companyName}</p>
            )}
          </div>
        </div>
        <Button onClick={onDownload} className="gap-2">
          <Download className="w-4 h-4" />
          Download Report
        </Button>
      </div>

      <div className="bg-muted/30 rounded-lg p-6 max-h-[400px] overflow-y-auto">
        <div className="flex items-center gap-2 mb-4 text-sm text-muted-foreground">
          <FileText className="w-4 h-4" />
          <span>Preview - {sections.length} sections extracted</span>
        </div>
        <div className="prose prose-sm max-w-none">
          <div className="text-foreground whitespace-pre-wrap font-mono text-xs">
            {markdown.substring(0, 1500)}
            {markdown.length > 1500 && '...'}
          </div>
        </div>
      </div>
    </Card>
  );
};
