import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_analysis

class TestBybitSpot(unittest.TestCase):

    @patch("bybit_spot_analysis.requests.get")
    def test_get_open_orders(self, mock_get):
        """Проверяем получение списка открытых ордеров"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {
                "list": [
                    {"orderId": "12345", "symbol": "BTCUSDT", "side": "Buy", "price": "5900.23", "orderStatus": "New"},
                    {"orderId": "67890", "symbol": "BTCUSDT", "side": "Sell", "price": "99726.88", "orderStatus": "PartiallyFilled"}
                ]
            }
        }
        mock_get.return_value = mock_response

        orders = bybit_spot_analysis.get_open_orders()
        self.assertEqual(len(orders), 2)  # Должны быть 2 ордера

    @patch("bybit_spot_analysis.requests.post")
    def test_cancel_order(self, mock_post):
        """Проверяем отмену одного ордера"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"retCode": 0, "retMsg": "OK", "result": {"orderId": "12345"}}
        mock_post.return_value = mock_response

        bybit_spot_analysis.cancel_order("12345")
        mock_post.assert_called_with(
            bybit_spot_analysis.CANCEL_ORDER_URL,
            json={
                "api_key": bybit_spot_analysis.API_KEY,
                "timestamp": mock_post.call_args[1]["json"]["timestamp"],  # Берем динамический timestamp
                "recv_window": str(bybit_spot_analysis.RECV_WINDOW),
                "orderId": "12345",
                "category": "spot",
                "sign": mock_post.call_args[1]["json"]["sign"],  # Берем динамическую подпись
            }
        )

    @patch("bybit_spot_analysis.requests.post")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_cancel_all_orders(self, mock_get_open_orders, mock_post):
        """Проверяем отмену всех ордеров (есть 2 ордера)"""
        mock_get_open_orders.return_value = [
            {"orderId": "12345"},
            {"orderId": "67890"}
        ]

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"retCode": 0, "retMsg": "OK", "result": {}}
        mock_post.return_value = mock_response

        bybit_spot_analysis.cancel_all_orders()

        # Должно быть 2 вызова `post()` (по числу ордеров)
        self.assertEqual(mock_post.call_count, 2)

    @patch("bybit_spot_analysis.requests.post")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_cancel_all_orders_no_orders(self, mock_get_open_orders, mock_post):
        """Проверяем отмену, когда ордеров нет (post() не должен вызываться)"""
        mock_get_open_orders.return_value = []  # Нет ордеров

        bybit_spot_analysis.cancel_all_orders()

        # Проверяем, что `post()` вообще не был вызван
        mock_post.assert_not_called()

if __name__ == "__main__":
    unittest.main()
