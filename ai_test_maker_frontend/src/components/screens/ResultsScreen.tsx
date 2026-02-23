import { Download, RotateCcw, PlusCircle, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TestResults } from '@/types/test';

interface ResultsScreenProps {
  results: TestResults;
  onRetake: () => void;
  onNewTest: () => void;
  onDownload: () => void;
}

export function ResultsScreen({ results, onRetake, onNewTest, onDownload }: ResultsScreenProps) {
  const percentage = results.total_marks > 0 ? (results.total_score / results.total_marks) * 100 : 0;
  const isPassing = percentage >= 50;

  return (
    <div className="min-h-screen pb-24">
      {/* Score Header */}
      <div className="glass-panel rounded-none border-x-0 border-t-0 px-6 py-8 mb-6">
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="text-2xl font-bold text-foreground mb-3">Test Results</h1>
          <p className={`text-4xl font-bold ${isPassing ? 'text-success' : 'text-destructive'}`}>
            {results.total_score} / {results.total_marks}
          </p>
          <p className={`text-lg font-medium ${isPassing ? 'text-success' : 'text-destructive'}`}>
            {percentage.toFixed(1)}%
          </p>
        </div>
      </div>

      {/* Results List */}
      <div className="max-w-4xl mx-auto px-6 space-y-4">
        {results.questions.map((result, idx) => {
          const isCorrect = result.marks_earned === result.marks_possible;
          const isPartial = result.marks_earned > 0 && !isCorrect;
          const borderClass = isCorrect ? 'border-success/50' : isPartial ? 'border-warning/50' : 'border-destructive/50';
          const Icon = isCorrect ? CheckCircle2 : isPartial ? AlertCircle : XCircle;
          const iconColor = isCorrect ? 'text-success' : isPartial ? 'text-warning' : 'text-destructive';

          return (
            <div
              key={idx}
              className={`glass-panel p-6 border-l-4 ${borderClass} animate-fade-in`}
              style={{ animationDelay: `${idx * 30}ms` }}
            >
              <div className="flex items-center gap-2 mb-3">
                <Icon className={`w-5 h-5 ${iconColor}`} />
                <span className={`font-semibold text-sm ${iconColor}`}>
                  Q{idx + 1}. {result.type} — {result.marks_earned}/{result.marks_possible} marks
                </span>
              </div>

              <p className="text-foreground mb-3">{result.question}</p>

              <div className="space-y-2 text-sm">
                <p className="text-muted-foreground">
                  <span className="font-medium">Your Answer:</span> {result.user_answer}
                </p>
                <p className="text-success">
                  <span className="font-medium">Correct Answer:</span> {result.correct_answer}
                </p>
                {result.feedback && (
                  <p className="text-warning italic">
                    <span className="font-medium">Feedback:</span> {result.feedback}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* Bottom Actions */}
      <div className="fixed bottom-0 inset-x-0 glass-panel rounded-none border-x-0 border-b-0 px-6 py-4">
        <div className="max-w-4xl mx-auto flex gap-3 justify-center">
          <Button variant="outline" onClick={onDownload}>
            <Download className="w-4 h-4 mr-2" />
            Download CSV
          </Button>
          <Button variant="outline" onClick={onRetake}>
            <RotateCcw className="w-4 h-4 mr-2" />
            Retake Test
          </Button>
          <Button onClick={onNewTest}>
            <PlusCircle className="w-4 h-4 mr-2" />
            New Test
          </Button>
        </div>
      </div>
    </div>
  );
}
