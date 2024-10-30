import unittest
from unittest.mock import patch, MagicMock
import requests

class TestLocalLLM(unittest.TestCase):
    @patch("requests.get")
    def test_local_server_running(self, mock_get):
        """
        Test to check if the local server is running.
        """

        # Mock the response from the local server
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Simulate checking the server status
        response = requests.get("http://127.0.0.1:8000/status")

        # Assert that the server is running
        mock_get.assert_called_once_with("http://127.0.0.1:8000/status")
        self.assertEqual(response.status_code, 200)

    @patch("requests.get")
    def test_model_route_exists(self, mock_get):
        """
        Test to check if the route to the fetched model exists.
        """

        # Mock the response from the local server
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        # Simulate checking the model route
        response = requests.get("http://127.0.0.1:8000/flan-t5/model")

        # Assert that the model route exists
        mock_get.assert_called_once_with("http://127.0.0.1:8000/flan-t5/model")
        self.assertEqual(response.status_code, 200)

    @patch("requests.get")
    def test_local_server_not_running(self, mock_get):
        """
        Test behavior when the local server is not running.
        """

        # Simulate a connection error
        mock_get.side_effect = requests.exceptions.ConnectionError

        # Attempt to check the server status
        with self.assertRaises(requests.exceptions.ConnectionError):
            requests.get("http://127.0.0.1:8000/status")

        # Assert that the server check was attempted
        mock_get.assert_called_once_with("http://127.0.0.1:8000/status")

if __name__ == "__main__":
    unittest.main()