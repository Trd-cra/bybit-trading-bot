import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_analysis

class TestCreateOrder(unittest.TestCase):

    @patch("bybit_spot_analysis.requests.post")
    def test_create_limit_order_success(self, mock_post):
        """Проверяем, что лимитный ордер создается успешно"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {"orderId": "12345"}
        }
        mock_post.return_value = mock_response

        order_id = bybit_spot_analysis.create_order("BTCUSDT", "Buy", "Limit", "5900.23", "0.1")
        self.assertEqual(order_id, "12345")
        mock_post.assert_called_once()

    @patch("bybit_spot_analysis.requests.post")
    def test_create_market_order_success(self, mock_post):
        """Проверяем, что маркет-ордер создается успешно"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {"orderId": "67890"}
        }
        mock_post.return_value = mock_response

        order_id = bybit_spot_analysis.create_order("BTCUSDT", "Sell", "Market", None, "0.5")
        self.assertEqual(order_id, "67890")
        mock_post.assert_called_once()

    @patch("bybit_spot_analysis.requests.post")
    def test_create_order_api_error(self, mock_post):
        """Проверяем, что бот не создает ордер, если API возвращает ошибку"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"retCode": 10002, "retMsg": "Invalid API Key"}
        mock_post.return_value = mock_response

        order_id = bybit_spot_analysis.create_order("BTCUSDT", "Buy", "Limit", "5900.23", "0.1")
        self.assertIsNone(order_id)
        mock_post.assert_called_once()

if __name__ == "__main__":
    unittest.main()
