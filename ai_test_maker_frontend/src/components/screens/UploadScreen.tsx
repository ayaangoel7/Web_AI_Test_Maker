import { useCallback, useRef } from 'react';
import { Upload, FileText, Brain } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { MARKS_OPTIONS } from '@/types/test';

interface UploadScreenProps {
  selectedFile: File | null;
  selectedMarks: number;
  onFileSelected: (file: File) => void;
  onMarksChanged: (marks: number) => void;
  onProceed: () => void;
  error: string | null;
}

export function UploadScreen({ selectedFile, selectedMarks, onFileSelected, onMarksChanged, onProceed, error }: UploadScreenProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) onFileSelected(file);
  }, [onFileSelected]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files?.[0];
    if (file && (file.name.endsWith('.pdf') || file.name.endsWith('.docx'))) {
      onFileSelected(file);
    }
  }, [onFileSelected]);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-2xl glass-panel p-10 animate-slide-up">
        {/* Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-primary/10 mb-4 glow-primary">
            <Brain className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-3xl font-bold text-foreground mb-2">AI Test Maker</h1>
          <p className="text-muted-foreground">Upload a PDF or Word document and generate a custom test</p>
        </div>

        {/* File Upload Zone */}
        <div
          className="border-2 border-dashed border-border rounded-xl p-8 text-center cursor-pointer hover:border-primary/50 transition-colors mb-8"
          onClick={() => fileInputRef.current?.click()}
          onDrop={handleDrop}
          onDragOver={(e) => e.preventDefault()}
        >
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.docx"
            className="hidden"
            onChange={handleFileChange}
          />
          {selectedFile ? (
            <div className="flex items-center justify-center gap-3">
              <FileText className="w-8 h-8 text-primary" />
              <div className="text-left">
                <p className="text-foreground font-medium">{selectedFile.name}</p>
                <p className="text-muted-foreground text-sm">{(selectedFile.size / 1024).toFixed(1)} KB</p>
              </div>
            </div>
          ) : (
            <>
              <Upload className="w-10 h-10 text-muted-foreground mx-auto mb-3" />
              <p className="text-muted-foreground">Click or drag to upload PDF/DOCX</p>
            </>
          )}
        </div>

        {/* Marks Selection */}
        <div className="mb-8">
          <h3 className="text-foreground font-semibold text-lg mb-4">Select Test Marks</h3>
          <div className="grid grid-cols-4 gap-3">
            {MARKS_OPTIONS.map((marks) => (
              <button
                key={marks}
                onClick={() => onMarksChanged(marks)}
                className={`py-3 px-4 rounded-lg font-semibold text-sm transition-all ${
                  selectedMarks === marks
                    ? 'bg-primary text-primary-foreground shadow-lg'
                    : 'bg-secondary text-secondary-foreground hover:bg-secondary/80'
                }`}
              >
                {marks} Marks
              </button>
            ))}
          </div>
        </div>

        {error && <p className="text-destructive text-sm mb-4">{error}</p>}

        {/* Proceed Button */}
        <Button
          className="w-full h-12 text-base font-semibold"
          onClick={onProceed}
          disabled={!selectedFile}
        >
          Next: Customize Questions
        </Button>
      </div>
    </div>
  );
}
