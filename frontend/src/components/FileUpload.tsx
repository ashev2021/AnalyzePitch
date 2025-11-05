import { useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Upload, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

interface FileUploadProps {
  onFileSelect: (file: File) => void;
  isProcessing?: boolean;
}

export const FileUpload = ({ onFileSelect, isProcessing }: FileUploadProps) => {
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      onFileSelect(acceptedFiles[0]);
    }
  }, [onFileSelect]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/vnd.ms-powerpoint': ['.ppt'],
      'application/vnd.openxmlformats-officedocument.presentationml.presentation': ['.pptx'],
    },
    maxFiles: 1,
    disabled: isProcessing,
  });

  return (
    <div
      {...getRootProps()}
      className={cn(
        'border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-all duration-300',
        'hover:border-primary hover:bg-accent/5',
        isDragActive && 'border-primary bg-accent/10',
        isProcessing && 'opacity-50 cursor-not-allowed'
      )}
    >
      <input {...getInputProps()} />
      <div className="flex flex-col items-center gap-4">
        {isDragActive ? (
          <>
            <FileText className="w-16 h-16 text-primary animate-pulse" />
            <p className="text-lg font-medium text-primary">Drop your pitch deck here</p>
          </>
        ) : (
          <>
            <Upload className="w-16 h-16 text-muted-foreground" />
            <div>
              <p className="text-lg font-medium text-foreground mb-2">
                Drop your pitch deck here, or click to browse
              </p>
              <p className="text-sm text-muted-foreground">
                Supports PDF, PPT, and PPTX files
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
