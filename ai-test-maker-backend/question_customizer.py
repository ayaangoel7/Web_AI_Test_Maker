"""
Question distribution customizer for test generation.
Allows users to override default question counts and validate against total marks.
"""


class QuestionCustomizer:
    """Handles question count customization and validation"""

    def __init__(self):
        # Question marks per type
        self.marks_per_type = {
            'MCQ': 1,
            'Very Short': 1,
            'Short(I)': 2,
            'Short(II)': 3,
            'Long Answer': 5,
        }

        # Default distributions by total marks
        self.default_distributions = {
            10: {
                'MCQ': 3, 'Very Short': 2, 'Short(I)': 1, 'Short(II)': 1, 'Long Answer': 0
            },
            25: {
                'MCQ': 8, 'Very Short': 3, 'Short(I)': 2, 'Short(II)': 3, 'Long Answer': 1
            },
            50: {
                'MCQ': 15, 'Very Short': 5, 'Short(I)': 4, 'Short(II)': 4, 'Long Answer': 2
            },
            100: {
                'MCQ': 30, 'Very Short': 10, 'Short(I)': 8, 'Short(II)': 8, 'Long Answer': 4
            },
        }

    def get_default_distribution(self, total_marks):
        """Get default question distribution for given total marks"""
        return self.default_distributions.get(
            total_marks,
            self.default_distributions[10]  # Fallback to 10 marks
        ).copy()

    def calculate_total_marks(self, distribution):
        """Calculate total marks from a distribution"""
        total = 0
        for q_type, count in distribution.items():
            total += count * self.marks_per_type.get(q_type, 1)
        return total

    def validate_distribution(self, distribution, expected_marks):
        """
        Validate that distribution totals to expected marks.
        Returns (is_valid, total_marks, error_message)
        """
        total_marks = self.calculate_total_marks(distribution)

        if total_marks == expected_marks:
            return True, total_marks, None
        elif total_marks < expected_marks:
            return False, total_marks, f"Total marks is {total_marks}, need {expected_marks}"
        else:
            return False, total_marks, f"Total marks is {total_marks}, exceeds {expected_marks}"

    def adjust_distribution(self, distribution, q_type, new_count, target_marks):
        """
        Adjust one question type count and validate.
        Returns (new_distribution, is_valid, total_marks, message)
        """
        # Create a copy to avoid modifying original
        new_dist = distribution.copy()
        
        # Ensure count is not negative
        if new_count < 0:
            return distribution, False, self.calculate_total_marks(distribution), "Count cannot be negative"

        old_count = distribution[q_type]
        new_dist[q_type] = new_count

        # Calculate new total
        total_marks = self.calculate_total_marks(new_dist)

        if total_marks > target_marks:
            return distribution, False, total_marks, f"Would exceed {target_marks} marks (current: {total_marks})"
        
        return new_dist, True, total_marks, None

    def get_question_types(self):
        """Get ordered list of question types"""
        return list(self.marks_per_type.keys())

    def get_marks_info(self, distribution):
        """Get detailed marks breakdown"""
        info = {}
        for q_type in self.get_question_types():
            count = distribution.get(q_type, 0)
            marks_per = self.marks_per_type[q_type]
            total = count * marks_per
            info[q_type] = {
                'count': count,
                'marks_per': marks_per,
                'total': total,
            }
        return info
