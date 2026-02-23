export interface QuestionDistribution {
  MCQ: number;
  'Very Short': number;
  'Short(I)': number;
  'Short(II)': number;
  'Long Answer': number;
}

export interface Question {
  type: string;
  marks: number;
  question: string;
  correct_answer: string;
  options?: string[];
}

export interface TestData {
  questions: Question[];
  total_marks: number;
  distribution: QuestionDistribution;
}

export interface QuestionResult {
  question: string;
  type: string;
  user_answer: string;
  correct_answer: string;
  marks_possible: number;
  marks_earned: number;
  feedback: string;
}

export interface TestResults {
  questions: QuestionResult[];
  total_score: number;
  total_marks: number;
}

export interface MarksPerType {
  [key: string]: number;
}

export const MARKS_PER_TYPE: MarksPerType = {
  MCQ: 1,
  'Very Short': 1,
  'Short(I)': 2,
  'Short(II)': 3,
  'Long Answer': 5,
};

export const QUESTION_TYPES = ['MCQ', 'Very Short', 'Short(I)', 'Short(II)', 'Long Answer'] as const;

export const DEFAULT_DISTRIBUTIONS: Record<number, QuestionDistribution> = {
  10: { MCQ: 3, 'Very Short': 2, 'Short(I)': 1, 'Short(II)': 1, 'Long Answer': 0 },
  25: { MCQ: 8, 'Very Short': 3, 'Short(I)': 2, 'Short(II)': 3, 'Long Answer': 1 },
  50: { MCQ: 15, 'Very Short': 5, 'Short(I)': 4, 'Short(II)': 4, 'Long Answer': 2 },
  100: { MCQ: 30, 'Very Short': 10, 'Short(I)': 8, 'Short(II)': 8, 'Long Answer': 4 },
};

export const MARKS_OPTIONS = [10, 25, 50, 100] as const;
