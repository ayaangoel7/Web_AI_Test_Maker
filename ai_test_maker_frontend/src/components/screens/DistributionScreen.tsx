import { useState, useCallback, useMemo } from 'react';
import { Minus, Plus, ArrowLeft, Sparkles } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  QuestionDistribution,
  QUESTION_TYPES,
  MARKS_PER_TYPE,
  DEFAULT_DISTRIBUTIONS,
} from '@/types/test';

interface DistributionScreenProps {
  totalMarks: number;
  onGenerate: (distribution: QuestionDistribution) => void;
  onBack: () => void;
}

export function DistributionScreen({ totalMarks, onGenerate, onBack }: DistributionScreenProps) {
  const [distribution, setDistribution] = useState<QuestionDistribution>(
    () => ({ ...(DEFAULT_DISTRIBUTIONS[totalMarks] ?? DEFAULT_DISTRIBUTIONS[10]) })
  );

  const currentTotal = useMemo(() => {
    return QUESTION_TYPES.reduce((sum, type) => {
      return sum + (distribution[type] || 0) * MARKS_PER_TYPE[type];
    }, 0);
  }, [distribution]);

  const isValid = currentTotal === totalMarks;
  const diff = totalMarks - currentTotal;

  const updateCount = useCallback((type: string, delta: number) => {
    setDistribution(prev => {
      const newCount = Math.max(0, Math.min(100, (prev[type as keyof QuestionDistribution] || 0) + delta));
      return { ...prev, [type]: newCount } as QuestionDistribution;
    });
  }, []);

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      <div className="w-full max-w-2xl glass-panel p-8 animate-slide-up">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-foreground mb-2">Customize Question Distribution</h1>
          <p className="text-muted-foreground">Total Marks: {totalMarks} • Adjust the number of each question type</p>
        </div>

        <div className="space-y-3 mb-6">
          {QUESTION_TYPES.map((type) => {
            const count = distribution[type] || 0;
            const marksForType = count * MARKS_PER_TYPE[type];
            return (
              <div key={type} className="flex items-center justify-between bg-secondary/50 rounded-lg px-5 py-4">
                <div>
                  <span className="text-foreground font-medium">{type}</span>
                  <span className="text-muted-foreground text-sm ml-2">
                    ({MARKS_PER_TYPE[type]} mark{MARKS_PER_TYPE[type] > 1 ? 's' : ''} each)
                  </span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-primary text-sm font-medium w-16 text-right">{marksForType} marks</span>
                  <button
                    onClick={() => updateCount(type, -1)}
                    className="w-8 h-8 rounded-md bg-muted flex items-center justify-center hover:bg-muted/80 transition-colors text-foreground"
                  >
                    <Minus className="w-4 h-4" />
                  </button>
                  <span className="w-8 text-center font-mono font-semibold text-foreground">{count}</span>
                  <button
                    onClick={() => updateCount(type, 1)}
                    className="w-8 h-8 rounded-md bg-muted flex items-center justify-center hover:bg-muted/80 transition-colors text-foreground"
                  >
                    <Plus className="w-4 h-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Total Display */}
        <div className="rounded-lg bg-secondary/30 p-4 text-center mb-6">
          <p className={`text-xl font-bold ${isValid ? 'text-success' : diff > 0 ? 'text-warning' : 'text-destructive'}`}>
            Total: {currentTotal} / {totalMarks} marks {isValid && '✓'}
          </p>
          {!isValid && (
            <p className={`text-sm mt-1 ${diff > 0 ? 'text-warning' : 'text-destructive'}`}>
              {diff > 0 ? `Need ${diff} more marks` : `Exceeds by ${Math.abs(diff)} marks`}
            </p>
          )}
        </div>

        {/* Buttons */}
        <div className="flex gap-3">
          <Button variant="outline" className="flex-1 h-11" onClick={onBack}>
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back
          </Button>
          <Button
            className="flex-1 h-11"
            disabled={!isValid}
            onClick={() => onGenerate(distribution)}
          >
            <Sparkles className="w-4 h-4 mr-2" />
            Generate Test
          </Button>
        </div>
      </div>
    </div>
  );
}
