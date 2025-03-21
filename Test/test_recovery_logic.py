import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_analysis
import time

class TestRecoveryLogic(unittest.TestCase):

    @patch("bybit_spot_analysis.requests.get")
    def test_api_reconnect_on_failure(self, mock_get):
        """Проверяем, что бот повторяет попытку подключения при сбое API"""
        mock_get.side_effect = [
            Exception("API недоступен"),
            MagicMock(status_code=200, json=lambda: {"retCode": 0, "time": 1741193247345})
        ]

        server_time = bybit_spot_analysis.sync_server_time()
        self.assertEqual(server_time, 1741193247345)

    @patch("bybit_spot_analysis.requests.get")
    def test_api_handles_http_errors(self, mock_get):
        """Проверяем, что бот обрабатывает ошибки 500/502 и не падает"""
        mock_get.side_effect = [
            MagicMock(status_code=500, text="Internal Server Error"),
            MagicMock(status_code=502, text="Bad Gateway"),
            MagicMock(status_code=200, json=lambda: {"retCode": 0, "time": 1741193247345})
        ]

        server_time = bybit_spot_analysis.sync_server_time()
        self.assertEqual(server_time, 1741193247345)

    @patch("bybit_spot_analysis.requests.get")
    def test_api_handles_retcode_errors(self, mock_get):
        """Проверяем, что бот корректно обрабатывает retCode != 0"""
        mock_get.side_effect = [
            MagicMock(status_code=200, json=lambda: {"retCode": 10002, "retMsg": "Invalid API Key"}),
            MagicMock(status_code=200, json=lambda: {"retCode": 0, "time": 1741193247345})
        ]

        server_time = bybit_spot_analysis.sync_server_time()
        self.assertEqual(server_time, 1741193247345)

    @patch("bybit_spot_analysis.requests.get")
    def test_bot_waits_before_reconnect(self, mock_get):
        """Проверяем, что бот ждет перед повторной попыткой"""
        with patch("time.sleep") as mock_sleep:
            mock_get.side_effect = [Exception("API недоступен"), MagicMock(status_code=200, json=lambda: {"retCode": 0, "time": 1741193247345})]

            server_time = bybit_spot_analysis.sync_server_time()
            self.assertEqual(server_time, 1741193247345)
            mock_sleep.assert_called_once_with(2)  # Бот должен был подождать 2 секунды перед повторной попыткой

if __name__ == "__main__":
    unittest.main()
