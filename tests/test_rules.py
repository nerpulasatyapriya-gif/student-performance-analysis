# Lightweight unit tests for the grading rule. Run with: python -m unittest discover -s tests
import unittest

def grade_for(percentage):
    if percentage >= 90: return "A"
    if percentage >= 80: return "B"
    if percentage >= 70: return "C"
    if percentage >= 60: return "D"
    if percentage >= 40: return "E"
    return "F"

class GradeRuleTests(unittest.TestCase):
    def test_boundaries(self):
        self.assertEqual(grade_for(100), "A")
        self.assertEqual(grade_for(89.9), "B")
        self.assertEqual(grade_for(79.9), "C")
        self.assertEqual(grade_for(69.9), "D")
        self.assertEqual(grade_for(40), "E")
        self.assertEqual(grade_for(39.9), "F")

if __name__ == "__main__":
    unittest.main()
