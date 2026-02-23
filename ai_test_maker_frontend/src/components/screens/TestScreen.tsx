import { useState, useCallback } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { TestData } from '@/types/test';

interface TestScreenProps {
  testData: TestData;
  onSubmit: (answers: Record<number, string>) => void;
}

export function TestScreen({ testData, onSubmit }: TestScreenProps) {
  const [answers, setAnswers] = useState<Record<number, string>>({});

  const updateAnswer = useCallback((num: number, value: string) => {
    setAnswers(prev => ({ ...prev, [num]: value }));
  }, []);

  const handleSubmit = useCallback(() => {
    onSubmit(answers);
  }, [answers, onSubmit]);

  return (
    <div className="min-h-screen pb-24">
      {/* Header */}
      <div className="sticky top-0 z-10 glass-panel rounded-none border-x-0 border-t-0 px-6 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-foreground">Take Your Test</h1>
            <p className="text-muted-foreground text-sm">
              Total Marks: {testData.total_marks} • Questions: {testData.questions.length}
            </p>
          </div>
          <Button onClick={handleSubmit} className="h-10">
            <Send className="w-4 h-4 mr-2" />
            Submit Test
          </Button>
        </div>
      </div>

      {/* Questions */}
      <div className="max-w-4xl mx-auto p-6 space-y-4">
        {testData.questions.map((question, idx) => {
          const num = idx + 1;
          return (
            <div key={num} className="glass-panel p-6 animate-fade-in" style={{ animationDelay: `${idx * 50}ms` }}>
              <div className="flex items-center gap-2 mb-3">
                <span className="text-primary font-semibold text-sm">
                  Q{num}. [{question.marks} mark{question.marks > 1 ? 's' : ''}] — {question.type}
                </span>
              </div>
              <p className="text-foreground mb-4 leading-relaxed">{question.question}</p>

              {question.type === 'MCQ' && question.options ? (
                <div className="space-y-2">
                  {question.options.map((option, oi) => (
                    <label
                      key={oi}
                      className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                        answers[num] === option
                          ? 'bg-primary/10 border border-primary/30'
                          : 'bg-secondary/30 hover:bg-secondary/50 border border-transparent'
                      }`}
                    >
                      <input
                        type="radio"
                        name={`q${num}`}
                        value={option}
                        checked={answers[num] === option}
                        onChange={() => updateAnswer(num, option)}
                        className="w-4 h-4 accent-primary"
                      />
                      <span className="text-foreground text-sm">{option}</span>
                    </label>
                  ))}
                </div>
              ) : question.type === 'Very Short' || question.type === 'Short(I)' ? (
                <input
                  type="text"
                  placeholder="Type your answer..."
                  value={answers[num] || ''}
                  onChange={(e) => updateAnswer(num, e.target.value)}
                  className="w-full bg-secondary/50 border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
                />
              ) : (
                <textarea
                  placeholder="Write your detailed answer..."
                  value={answers[num] || ''}
                  onChange={(e) => updateAnswer(num, e.target.value)}
                  rows={question.type === 'Long Answer' ? 6 : 4}
                  className="w-full bg-secondary/50 border border-border rounded-lg px-4 py-3 text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50 resize-y"
                />
              )}
            </div>
          );
        })}
      </div>

      {/* Bottom Submit */}
      <div className="fixed bottom-0 inset-x-0 glass-panel rounded-none border-x-0 border-b-0 px-6 py-4">
        <div className="max-w-4xl mx-auto flex justify-between items-center">
          <p className="text-muted-foreground text-sm">
            Answered: {Object.keys(answers).filter(k => answers[Number(k)]?.trim()).length} / {testData.questions.length}
          </p>
          <Button onClick={handleSubmit} size="lg">
            <Send className="w-4 h-4 mr-2" />
            Submit Test
          </Button>
        </div>
      </div>
    </div>
  );
}
