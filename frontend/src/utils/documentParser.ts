export interface ParsedDocument {
  text: string;
  metadata: {
    fileName: string;
    fileType: string;
    pageCount?: number;
  };
}

export const parseDocument = async (file: File): Promise<ParsedDocument> => {
  // This is a simplified parser - in production, you'd use libraries like pdf.js or mammoth
  // For now, we'll simulate parsing with the file metadata
  
  return new Promise((resolve) => {
    const reader = new FileReader();
    
    reader.onload = () => {
      // Simulated extraction - in real app, parse actual content
      const metadata = {
        fileName: file.name,
        fileType: file.type,
        pageCount: Math.floor(Math.random() * 30) + 10, // Simulated
      };

      // Simulated text content
      const text = `Extracted content from ${file.name}`;
      
      resolve({
        text,
        metadata,
      });
    };
    
    reader.readAsArrayBuffer(file);
  });
};
