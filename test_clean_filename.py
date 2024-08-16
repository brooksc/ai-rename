import unittest
from ai_rename import clean_filename

class TestCleanFilename(unittest.TestCase):

    def test_clean_filename(self):
        # Test cases with valid filenames
        self.assertEqual(clean_filename("ValidFilename"), "ValidFilename")
        self.assertEqual(clean_filename("Valid Filename"), "Valid Filename")
        self.assertEqual(clean_filename("Valid_Filename"), "Valid Filename")
        self.assertEqual(clean_filename("Valid-Filename"), "Valid Filename")
        self.assertEqual(clean_filename("ValidFilename123"), "ValidFilename123")

        # Test cases with invalid characters
        self.assertEqual(clean_filename("Invalid*Filename!"), "Invalid Filename")
        self.assertEqual(clean_filename("Invalid#Filename$"), "Invalid Filename")
        self.assertEqual(clean_filename("Invalid@Filename%"), "Invalid Filename")
        self.assertEqual(clean_filename("Invalid^Filename&"), "Invalid Filename")
        self.assertEqual(clean_filename("Invalid*Filename!"), "Invalid Filename")

        # Test cases with multiple spaces and underscores
        self.assertEqual(clean_filename("Too   Many   Spaces"), "Too Many Spaces")
        self.assertEqual(clean_filename("Too___Many___Underscores"), "Too Many Underscores")
        self.assertEqual(clean_filename("Mixed   Spaces_And_Underscores"), "Mixed Spaces And Underscores")

        # Test cases with camel case
        self.assertEqual(clean_filename("camelCaseFilename"), "camel Case Filename")
        self.assertEqual(clean_filename("PascalCaseFilename"), "Pascal Case Filename")

        # Test cases with file extensions
        self.assertEqual(clean_filename("FilenameWithExtension.pdf"), "FilenameWithExtension")
        self.assertEqual(clean_filename("Filename With Extension.pdf"), "Filename With Extension")
        self.assertEqual(clean_filename("Filename_With_Extension.pdf"), "Filename With Extension")

        # Test cases with very long filenames
        self.assertIsNone(clean_filename("A" * 101))
        self.assertIsNone(clean_filename("B" * 150))

        # Test cases with very short filenames
        self.assertIsNone(clean_filename("A"))
        self.assertIsNone(clean_filename("BB"))

if __name__ == '__main__':
    unittest.main()
