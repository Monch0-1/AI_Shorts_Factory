
import unittest
from unittest.mock import patch, MagicMock

# Import the functions to be tested
from CreateShorts.ContextualDataService.ContextualDataGenerator import perform_google_search, get_fresh_context

class TestContextualDataGenerator(unittest.TestCase):
    def test_perform_google_search(self, mock_build):
        # Arrange
        mock_service = MagicMock()
        mock_cse = MagicMock()
        mock_service.cse.return_value = mock_cse
        mock_build.return_value = mock_service

        expected_items = [
            {'title': 'Test Title 1', 'snippet': 'Test Snippet 1'},
            {'title': 'Test Title 2', 'snippet': 'Test Snippet 2'}
        ]
        mock_cse.list().execute.return_value = {'items': expected_items}

        # Act
        results = perform_google_search('test query')

        # Assert
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0], "Title: Test Title 1 | Snippet: Test Snippet 1")
        self.assertEqual(results[1], "Title: Test Title 2 | Snippet: Test Snippet 2")
        mock_build.assert_called_once_with("customsearch", "v1", developerKey=None)
        mock_cse.list.assert_called_once_with(q='test query', cx=None, num=5)

    @patch('ContextualDataService.ContextualDataGenerator.perform_google_search')
    @patch('ContextualDataService.ContextualDataGenerator.model')
    def test_get_fresh_context(self, mock_model, mock_perform_google_search):
        # Arrange
        mock_perform_google_search.return_value = ["Title: Test Title | Snippet: Test Snippet"]
        
        mock_response = MagicMock()
        mock_response.text = "This is the distilled context."
        mock_model.generate_content.return_value = mock_response

        # Act
        context = get_fresh_context("test topic")

        # Assert
        self.assertEqual(context, "This is the distilled context.")
        self.assertEqual(mock_perform_google_search.call_count, 2)
        mock_model.generate_content.assert_called_once()

    @patch('ContextualDataService.ContextualDataGenerator.perform_google_search')
    def test_get_fresh_context_no_snippets(self, mock_perform_google_search):
        # Arrange
        mock_perform_google_search.return_value = []

        # Act
        context = get_fresh_context("test topic")

        # Assert
        self.assertEqual(context, "")

if __name__ == '__main__':
    unittest.main()
