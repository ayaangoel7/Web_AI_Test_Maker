import { Loader2 } from 'lucide-react';
import { Progress } from '@/components/ui/progress';

interface LoadingScreenProps {
  message: string;
  progress: number;
}

export function LoadingScreen({ message, progress }: LoadingScreenProps) {
  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="text-center max-w-md">
        <Loader2 className="w-12 h-12 text-primary mx-auto mb-6 animate-spin" />
        <p className="text-foreground text-lg whitespace-pre-line mb-6">{message}</p>
        <Progress value={progress * 100} className="h-2" />
        <p className="text-muted-foreground text-sm mt-3">{Math.round(progress * 100)}%</p>
      </div>
    </div>
  );
}
