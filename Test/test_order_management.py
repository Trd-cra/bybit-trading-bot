import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_analysis

class TestOrderManagement(unittest.TestCase):

    @patch("bybit_spot_analysis.requests.get")
    def test_get_open_orders(self, mock_get):
        """Проверяем получение списка открытых ордеров"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "retCode": 0,
            "retMsg": "OK",
            "result": {"list": [{"orderId": "12345"}, {"orderId": "67890"}]}
        }
        mock_get.return_value = mock_response

        orders = bybit_spot_analysis.get_open_orders()
        self.assertEqual(len(orders), 2)

    @patch("bybit_spot_analysis.requests.post")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_cancel_all_orders(self, mock_get_open_orders, mock_post):
        """Создаем ордера перед отменой, затем отменяем их"""
        
        # Создаем фиктивные ордера
        with patch("bybit_spot_analysis.create_order") as mock_create_order:
            mock_create_order.side_effect = ["12345", "67890"]
            bybit_spot_analysis.create_order("BTCUSDT", "Buy", "Limit", "5900.23", "0.1")
            bybit_spot_analysis.create_order("ETHUSDT", "Sell", "Market", None, "0.5")

        # Теперь бот должен их видеть в списке открытых ордеров
        mock_get_open_orders.return_value = [
            {"orderId": "12345", "orderStatus": "New"},
            {"orderId": "67890", "orderStatus": "PartiallyFilled"}
        ]

        # Мок успешного удаления
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"retCode": 0, "retMsg": "OK", "result": {}}
        mock_post.return_value = mock_response

        bybit_spot_analysis.cancel_all_orders()
        self.assertEqual(mock_post.call_count, 2)

    @patch("bybit_spot_analysis.requests.post")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_cancel_filled_or_cancelled_orders(self, mock_get_open_orders, mock_post):
        """Проверяем, что бот не пытается отменять исполненные (`Filled`) и отмененные (`Cancelled`) ордера"""
        mock_get_open_orders.return_value = [
            {"orderId": "12345", "orderStatus": "Filled"},
            {"orderId": "67890", "orderStatus": "Cancelled"}
        ]

        bybit_spot_analysis.cancel_all_orders()
        mock_post.assert_not_called()

if __name__ == "__main__":
    unittest.main()
