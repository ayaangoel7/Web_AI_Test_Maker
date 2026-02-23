import re
from difflib import SequenceMatcher
import numpy as np

class TestGrader:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine

    def grade_test(self, test_data, user_answers):
        results = {
            'questions': [],
            'total_score': 0,
            'total_marks': test_data['total_marks']
        }

        for i, question in enumerate(test_data['questions'], 1):
            user_answer = user_answers.get(i, "")

            # Grade based on question type
            if question['type'] == 'MCQ':
                result = self.grade_mcq(question, user_answer)
            elif question['type'] == 'Very Short':
                result = self.grade_semantic(question, user_answer, length_weight=0.3)
            elif question['type'] in ['Short(I)', 'Short(II)']:
                result = self.grade_semantic(question, user_answer, length_weight=0.5)
            else:  # Long Answer
                result = self.grade_long_answer(question, user_answer)

            # Accumulate rounded score
            results['questions'].append(result)
            results['total_score'] += result['marks_earned']

        # Final score is sum of rounded marks, so it will be clean.
        return results

    def _round_to_half(self, marks):
        """Rounds marks to the nearest 0.5."""
        return round(marks * 2) / 2

    def grade_mcq(self, question, user_answer):
        correct = question['correct_answer'].strip()
        user = user_answer.strip()
        is_correct = correct.lower() == user.lower()

        return {
            'question': question['question'],
            'type': question['type'],
            'user_answer': user_answer if user_answer else "No answer",
            'correct_answer': correct,
            'marks_possible': question['marks'],
            'marks_earned': question['marks'] if is_correct else 0,
            'feedback': 'Correct!' if is_correct else f'Incorrect. The correct answer is {correct}'
        }

    def grade_semantic(self, question, user_answer, length_weight=0.5):
        if not user_answer or not user_answer.strip():
            return {
                'question': question['question'], 'type': question['type'],
                'user_answer': 'No answer', 'correct_answer': question['correct_answer'],
                'marks_possible': question['marks'], 'marks_earned': 0,
                'feedback': 'No answer provided'
            }

        try:
            # FIX #1: Anti-cheat check. Compare the user's answer to the question itself.
            question_emb = self.ai_engine.get_embeddings(question['question'])
            user_emb = self.ai_engine.get_embeddings(user_answer)
            question_answer_similarity = self.ai_engine.compute_similarity(question_emb, user_emb)

            if question_answer_similarity > 0.9:
                return {
                    'question': question['question'], 'type': question['type'],
                    'user_answer': user_answer, 'correct_answer': question['correct_answer'],
                    'marks_possible': question['marks'], 'marks_earned': 0,
                    'feedback': 'The answer appears to be a copy of the question and has been awarded 0 marks.'
                }

            # Grade against the correct answer
            correct_emb = self.ai_engine.get_embeddings(question['correct_answer'])
            semantic_similarity = self.ai_engine.compute_similarity(user_emb, correct_emb)

            # Calculate length ratio
            user_len = len(user_answer.split())
            correct_len = len(question['correct_answer'].split())
            length_ratio = min(1.0, user_len / correct_len) if correct_len > 0 else 0

            # Combine scores based on semantic similarity and length
            if semantic_similarity > 0.65:
                final_score_ratio = (semantic_similarity * (1 - length_weight)) + (length_ratio * length_weight)
                final_score_ratio = max(semantic_similarity, final_score_ratio)
                feedback = 'Good answer, but it could be more detailed.' if length_ratio < 0.7 else 'Excellent answer!'
            elif semantic_similarity > 0.4:
                final_score_ratio = semantic_similarity * 0.5 # Reduced marks for partial concepts
                feedback = 'Partially correct, but missing some key points.'
            else:
                final_score_ratio = 0
                feedback = 'The answer does not seem to address the key points of the question.'
            
            final_score_ratio = min(1.0, final_score_ratio)
            raw_marks = question['marks'] * final_score_ratio
            # FIX #2: Round marks to nearest 0.5
            marks_earned = self._round_to_half(raw_marks)

        except Exception:
            marks_earned = 0
            feedback = 'Could not evaluate answer due to an error.'

        return {
            'question': question['question'], 'type': question['type'],
            'user_answer': user_answer, 'correct_answer': question['correct_answer'],
            'marks_possible': question['marks'], 'marks_earned': marks_earned,
            'feedback': feedback
        }

    def grade_long_answer(self, question, user_answer):
        if not user_answer or not user_answer.strip():
            return {
                'question': question['question'], 'type': question['type'],
                'user_answer': 'No answer', 'correct_answer': question['correct_answer'],
                'marks_possible': question['marks'], 'marks_earned': 0,
                'feedback': 'No answer provided'
            }

        try:
            # FIX #1: Anti-cheat check before calling the expensive LLM
            question_emb = self.ai_engine.get_embeddings(question['question'])
            user_emb = self.ai_engine.get_embeddings(user_answer)
            question_answer_similarity = self.ai_engine.compute_similarity(question_emb, user_emb)
            if question_answer_similarity > 0.9:
                return {
                    'question': question['question'], 'type': question['type'],
                    'user_answer': user_answer, 'correct_answer': question['correct_answer'],
                    'marks_possible': question['marks'], 'marks_earned': 0,
                    'feedback': 'The answer appears to be a copy of the question and has been awarded 0 marks.'
                }

            prompt = f"""
Grade the student's answer for a question worth {question['marks']} marks.

Question: {question['question']}
Ideal Answer: {question['correct_answer']}
Student's Answer: {user_answer}

Evaluate based on accuracy, completeness for the given marks, and clarity.

Provide your response ONLY in this format:
Score: [score out of {question['marks']}]
Feedback: [brief, constructive feedback]
"""
            response = self.ai_engine.generate_text(prompt, max_tokens=200, temperature=0.2)
            score_match = re.search(r'Score:\s*(\d+\.?\d*)', response)
            feedback_match = re.search(r'Feedback:\s*(.+)', response, re.DOTALL)

            if score_match:
                raw_marks = min(float(score_match.group(1)), question['marks'])
                # FIX #2: Round marks to nearest 0.5
                marks_earned = self._round_to_half(raw_marks)
            else:
                raise ValueError("LLM did not return a score.")
            
            feedback = feedback_match.group(1).strip() if feedback_match else "No specific feedback provided."

        except Exception:
            # Fallback to semantic grader if LLM fails
            result = self.grade_semantic(question, user_answer, length_weight=0.6)
            marks_earned = result['marks_earned'] # Already rounded
            feedback = f"AI grader fallback: {result['feedback']}"

        return {
            'question': question['question'], 'type': question['type'],
            'user_answer': user_answer[:250] + '...' if len(user_answer) > 250 else user_answer,
            'correct_answer': question['correct_answer'][:250] + '...' if len(question['correct_answer']) > 250 else question['correct_answer'],
            'marks_possible': question['marks'], 'marks_earned': marks_earned, 'feedback': feedback
        }
