import json
import random
import re
import itertools


class TestGenerator:
    def __init__(self, ai_engine):
        self.ai_engine = ai_engine

        # Question distribution templates (defaults)
        self.distributions = {
            10: {
                'MCQ': 3, 'Very Short': 2, 'Short(I)': 1, 'Short(II)': 1, 'Long Answer': 0
            },
            25: {
                'MCQ': 7, 'Very Short': 3, 'Short(I)': 2, 'Short(II)': 2, 'Long Answer': 1
            },
            50: {
                'MCQ': 15, 'Very Short': 5, 'Short(I)': 4, 'Short(II)': 4, 'Long Answer': 2
            },
            100: {
                'MCQ': 30, 'Very Short': 10, 'Short(I)': 8, 'Short(II)': 8, 'Long Answer': 4
            }
        }

        self.marks_per_type = {
            'MCQ': 1,
            'Very Short': 1,
            'Short(I)': 2,
            'Short(II)': 3,
            'Long Answer': 5
        }

    def generate_test(self, content, marks):
        """Generate test using default distribution"""
        distribution = self.distributions[marks]
        return self._generate_with_distribution(content, marks, distribution)

    def generate_test_custom(self, content, marks, custom_distribution):
        """Generate test using custom distribution"""
        return self._generate_with_distribution(content, marks, custom_distribution)

    def _generate_with_distribution(self, content, marks, distribution):
        """
        Internal method to generate test with any distribution.
        This new implementation processes the document chunk-by-chunk to stay within token limits.
        """
        text_chunks = content['text_chunks']
        if not text_chunks:
            return {'questions': [], 'total_marks': marks, 'distribution': distribution}

        images = content.get('images', [])
        questions = []
        needed_counts = distribution.copy()

        # Create a list of question types that we need to generate
        q_types_in_play = [q_type for q_type, count in needed_counts.items() if count > 0]
        if not q_types_in_play:
            return {'questions': [], 'total_marks': 0, 'distribution': {}}

        # Cycle through question types and shuffled chunk indices to ensure variety
        type_cycler = itertools.cycle(q_types_in_play)
        chunk_indices = list(range(len(text_chunks)))
        random.shuffle(chunk_indices)
        chunk_cycler = itertools.cycle(chunk_indices)

        # Set a safe upper bound on iterations to prevent infinite loops
        max_iterations = sum(needed_counts.values()) * 2
        current_iteration = 0

        while sum(needed_counts.values()) > 0 and current_iteration < max_iterations:
            current_iteration += 1

            # Get the next question type we need to generate, skipping those we've finished
            try:
                q_type = next(type_cycler)
                while needed_counts[q_type] <= 0:
                    q_type = next(type_cycler)
            except StopIteration:
                break  # Should not happen with cycle, but as a safeguard

            # Get the next chunk of text to process
            chunk_index = next(chunk_cycler)
            text_chunk = text_chunks[chunk_index]

            # Determine how many questions to ask for in this single call (a small number)
            num_to_ask = min(needed_counts[q_type], random.randint(1, 2))

            if num_to_ask > 0:
                print(f"Generating {num_to_ask} '{q_type}' questions from chunk {chunk_index + 1}/{len(text_chunks)}...")

                # Generate questions from the single chunk
                type_questions = self.generate_questions_of_type(
                    text_chunk,
                    q_type,
                    num_to_ask,
                    images
                )

                # Add generated questions and update the count of what's still needed
                if type_questions:
                    questions.extend(type_questions)
                    needed_counts[q_type] -= len(type_questions)

        # Re-calculate the final marks and distribution based on what was actually generated
        final_distribution = {}
        final_marks = 0
        for q in questions:
            q_type = q['type']
            final_distribution[q_type] = final_distribution.get(q_type, 0) + 1
        
        # Calculate marks based on the new final distribution
        for q_type, count in final_distribution.items():
            final_marks += self.marks_per_type.get(q_type, 0) * count

        random.shuffle(questions)

        return {
            'questions': questions,
            'total_marks': final_marks,
            'distribution': final_distribution
        }

    def generate_questions_of_type(self, text, q_type, count, images):
        marks = self.marks_per_type[q_type]

        prompt_base = f"""Based on the provided text, generate exactly {count} {q_type} questions.
Your response MUST be ONLY a valid JSON array of objects enclosed in a ```json markdown block. Do not include any other text, titles, or explanations before or after the JSON block.

Text:
---
{text}

"""
        if q_type == "MCQ":
            prompt = prompt_base + f"Each object in the JSON array must have these fields: 'question' (string), 'options' (array of 4 strings), 'correct_answer' (string), and 'explanation' (string)."
        elif q_type == "Very Short":
            prompt = prompt_base + f"Each object in the JSON array must have these fields: 'question' (string), 'correct_answer' (string), and 'keywords' (string of comma-separated keywords)."
        elif q_type == "Short(I)":
            prompt = prompt_base + f"Each object in the JSON array must have these fields: 'question' (string), 'correct_answer' (string, 2-3 sentences), and 'key_points' (array of strings)."
        elif q_type == "Short(II)":
            prompt = prompt_base + f"Each object in the JSON array must have these fields: 'question' (string), 'correct_answer' (string, 4-5 sentences), and 'key_concepts' (array of strings)."
        else:  # Long Answer
            prompt = prompt_base + f"Each object in the JSON array must have these fields: 'question' (string), 'correct_answer' (string, a detailed paragraph), 'key_themes' (array of strings), and 'evaluation_criteria' (array of strings)."

        try:
            response = self.ai_engine.generate_text(prompt)

            questions_data = self.extract_json(response, count)
            
            if not questions_data:
                print(f"Warning: Failed to extract valid JSON for {q_type} from model response.")
                return []

            formatted_questions = []
            for q_data in questions_data:
                if not q_data.get('question') or not q_data.get('correct_answer'):
                    continue

                question = {
                    'type': q_type,
                    'marks': marks,
                    'question': q_data['question'],
                    'correct_answer': q_data['correct_answer'],
                }

                if q_type == "MCQ":
                    question['options'] = q_data.get('options', [])
                    if len(question['options']) != 4:
                        continue 
                    
                    if images and random.random() < 0.15:
                        question['image'] = random.choice(images)

                formatted_questions.append(question)

            return formatted_questions

        except Exception as e:
            print(f"Error generating {q_type} questions: {e}")
            return self.generate_fallback_questions(q_type, count, marks)

    def extract_json(self, text, expected_count):
        """
        Extracts a JSON array from the model's text response.
        It first looks for a markdown JSON block and falls back to finding the first array.
        """
        match = re.search(r"```json\s*(\[.*\])\s*```", text, re.DOTALL)
        if match:
            json_str = match.group(1)
        else:
            start = text.find('[')
            end = text.rfind(']') + 1
            if start != -1 and end > start:
                json_str = text[start:end]
            else:
                return []

        try:
            data = json.loads(json_str)
            if isinstance(data, list):
                return data[:expected_count]
        except json.JSONDecodeError as e:
            print(f"JSON Decode Error: {e}\nRaw text was:\n---\n{text}\n---")
            return []
        
        return []

    def generate_fallback_questions(self, q_type, count, marks):
        """
        Fallback function. Now returns an empty list to prevent placeholder questions
        from appearing in the final test.
        """
        print(f"Executing fallback for {q_type} - returning no questions for this attempt.")
        return []
