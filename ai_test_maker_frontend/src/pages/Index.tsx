import { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { TestData, TestResults, QuestionDistribution } from '@/types/test';
import { UploadScreen } from '@/components/screens/UploadScreen';
import { DistributionScreen } from '@/components/screens/DistributionScreen';
import { TestScreen } from '@/components/screens/TestScreen';
import { ResultsScreen } from '@/components/screens/ResultsScreen';
import { LoadingScreen } from '@/components/screens/LoadingScreen';
import { apiService } from '@/services/api';

type AppScreen = 'upload' | 'distribution' | 'loading' | 'test' | 'grading' | 'results';

const Index = () => {
  const [screen, setScreen] = useState<AppScreen>('upload');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [fileId, setFileId] = useState<string>('');
  const [selectedMarks, setSelectedMarks] = useState<number>(10);
  const [distribution, setDistribution] = useState<QuestionDistribution | null>(null);
  const [testData, setTestData] = useState<TestData | null>(null);
  const [results, setResults] = useState<TestResults | null>(null);
  const [loadingMessage, setLoadingMessage] = useState('');
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const handleFileSelected = useCallback((file: File) => {
    setSelectedFile(file);
    setError(null);
  }, []);

  const handleProceedToDistribution = useCallback(async () => {
    if (!selectedFile) return;
    try {
      setScreen('loading');
      setLoadingMessage('Uploading file...');
      setLoadingProgress(0.3);
      const result = await apiService.uploadFile(selectedFile);
      setFileId(result.file_id);
      setScreen('distribution');
    } catch (err) {
      // In demo mode, proceed without actual upload
      setFileId('demo-file');
      setScreen('distribution');
    }
  }, [selectedFile]);

  const handleGenerateTest = useCallback(async (dist: QuestionDistribution) => {
    setDistribution(dist);
    setScreen('loading');
    setLoadingMessage('Generating test questions with AI...\nThis may take 30-60 seconds.');
    setLoadingProgress(0);

    try {
      const interval = setInterval(() => {
        setLoadingProgress(prev => Math.min(prev + 0.05, 0.9));
      }, 2000);

      const data = await apiService.generateTest(fileId, selectedMarks, dist as unknown as Record<string, number>);
      clearInterval(interval);
      setTestData(data);
      setLoadingProgress(1);
      setTimeout(() => setScreen('test'), 500);
    } catch {
      // Demo mode: generate sample questions
      const demoTest = generateDemoTest(dist, selectedMarks);
      setTestData(demoTest);
      setScreen('test');
    }
  }, [fileId, selectedMarks]);

  const handleSubmitTest = useCallback(async (answers: Record<number, string>) => {
    if (!testData) return;
    setScreen('grading');
    setLoadingMessage('Grading your answers with AI...');
    setLoadingProgress(0);

    try {
      const interval = setInterval(() => {
        setLoadingProgress(prev => Math.min(prev + 0.1, 0.9));
      }, 500);

      const gradeResults = await apiService.gradeTest(testData, answers);
      clearInterval(interval);
      setResults(gradeResults);
      setLoadingProgress(1);
      setTimeout(() => setScreen('results'), 500);
    } catch {
      // Demo grading
      const demoResults = gradeDemoTest(testData, answers);
      setResults(demoResults);
      setScreen('results');
    }
  }, [testData]);

  const handleRetakeTest = useCallback(() => {
    setScreen('test');
  }, []);

  const handleNewTest = useCallback(() => {
    setSelectedFile(null);
    setFileId('');
    setTestData(null);
    setResults(null);
    setDistribution(null);
    setScreen('upload');
  }, []);

  const handleDownloadResults = useCallback(() => {
    if (!results) return;
    const lines = ['Question,Type,Marks Earned,Marks Possible,User Answer,Correct Answer,Feedback'];
    results.questions.forEach((r, i) => {
      lines.push(`"${i + 1}","${r.type}","${r.marks_earned}","${r.marks_possible}","${r.user_answer}","${r.correct_answer}","${r.feedback}"`);
    });
    lines.push(`\nTotal Score,${results.total_score}/${results.total_marks}`);
    const blob = new Blob([lines.join('\n')], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `test_results_${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [results]);

  return (
    <div className="min-h-screen bg-background">
      <AnimatePresence mode="wait">
        {screen === 'upload' && (
          <motion.div key="upload" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
            <UploadScreen
              selectedFile={selectedFile}
              selectedMarks={selectedMarks}
              onFileSelected={handleFileSelected}
              onMarksChanged={setSelectedMarks}
              onProceed={handleProceedToDistribution}
              error={error}
            />
          </motion.div>
        )}
        {screen === 'distribution' && (
          <motion.div key="distribution" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
            <DistributionScreen
              totalMarks={selectedMarks}
              onGenerate={handleGenerateTest}
              onBack={() => setScreen('upload')}
            />
          </motion.div>
        )}
        {(screen === 'loading' || screen === 'grading') && (
          <motion.div key="loading" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.3 }}>
            <LoadingScreen message={loadingMessage} progress={loadingProgress} />
          </motion.div>
        )}
        {screen === 'test' && testData && (
          <motion.div key="test" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
            <TestScreen testData={testData} onSubmit={handleSubmitTest} />
          </motion.div>
        )}
        {screen === 'results' && results && (
          <motion.div key="results" initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -20 }} transition={{ duration: 0.3 }}>
            <ResultsScreen
              results={results}
              onRetake={handleRetakeTest}
              onNewTest={handleNewTest}
              onDownload={handleDownloadResults}
            />
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

// Demo helpers for when backend is not connected
function generateDemoTest(dist: QuestionDistribution, totalMarks: number): TestData {
  const questions: TestData['questions'] = [];

  const addQuestions = (type: string, count: number, marks: number) => {
    for (let i = 0; i < count; i++) {
      const q: any = {
        type,
        marks,
        question: `Sample ${type} question ${i + 1}: What is the main concept discussed in the uploaded document?`,
        correct_answer: type === 'MCQ' ? 'A) The primary concept' : 'The primary concept discussed involves the fundamental principles outlined in the document.',
      };
      if (type === 'MCQ') {
        q.options = ['A) The primary concept', 'B) A secondary idea', 'C) An unrelated topic', 'D) None of the above'];
      }
      questions.push(q);
    }
  };

  addQuestions('MCQ', dist.MCQ, 1);
  addQuestions('Very Short', dist['Very Short'], 1);
  addQuestions('Short(I)', dist['Short(I)'], 2);
  addQuestions('Short(II)', dist['Short(II)'], 3);
  addQuestions('Long Answer', dist['Long Answer'], 5);

  return { questions, total_marks: totalMarks, distribution: dist };
}

function gradeDemoTest(testData: TestData, answers: Record<number, string>): TestResults {
  const results: TestResults = { questions: [], total_score: 0, total_marks: testData.total_marks };

  testData.questions.forEach((q, i) => {
    const userAnswer = answers[i + 1] || 'No answer';
    const hasAnswer = userAnswer.trim() !== '' && userAnswer !== 'No answer';
    const earned = hasAnswer ? Math.round(q.marks * 0.7 * 10) / 10 : 0;
    results.questions.push({
      question: q.question,
      type: q.type,
      user_answer: userAnswer,
      correct_answer: q.correct_answer,
      marks_possible: q.marks,
      marks_earned: earned,
      feedback: hasAnswer ? 'Good attempt! (Demo grading)' : 'No answer provided',
    });
    results.total_score += earned;
  });

  results.total_score = Math.round(results.total_score * 10) / 10;
  return results;
}

export default Index;
