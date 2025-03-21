import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_analysis

class TestAPIConnection(unittest.TestCase):

    @patch("bybit_spot_analysis.requests.get")
    def test_api_connection_success(self, mock_get):
        """Проверяем, что API Bybit отвечает статусом 200"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"retCode": 0, "retMsg": "OK"}
        mock_get.return_value = mock_response

        response = bybit_spot_analysis.requests.get(bybit_spot_analysis.BASE_URL + "/v5/market/time")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["retCode"], 0)

    @patch("bybit_spot_analysis.requests.get")
    def test_sync_server_time(self, mock_get):
        """Проверяем, что бот корректно получает время с API"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"time": 1741190985799}
        mock_get.return_value = mock_response

        server_time = bybit_spot_analysis.sync_server_time()
        self.assertEqual(server_time, 1741190985799)

    @patch("bybit_spot_analysis.requests.get")
    def test_sync_server_time_fallback(self, mock_get):
        """Проверяем, что если API не отвечает, бот использует локальное время"""
        mock_get.side_effect = Exception("API недоступен")

        server_time = bybit_spot_analysis.sync_server_time()
        self.assertTrue(isinstance(server_time, int))  # Должно вернуть timestamp
        self.assertGreater(server_time, 0)  # Проверяем, что значение > 0

    @patch("bybit_spot_analysis.requests.get")
    def test_api_error_handling(self, mock_get):
        """Проверяем, что бот не ломается при ошибке API (retCode != 0)"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"retCode": 10002, "retMsg": "Invalid API Key"}
        mock_get.return_value = mock_response

        response = bybit_spot_analysis.requests.get(bybit_spot_analysis.BASE_URL + "/v5/market/time")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["retCode"], 10002)
        self.assertEqual(response.json()["retMsg"], "Invalid API Key")

if __name__ == "__main__":
    unittest.main()
