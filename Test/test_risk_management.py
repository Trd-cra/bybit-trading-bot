import unittest
from unittest.mock import patch
from bybit_spot_analysis import handle_risk_management, create_order, cancel_all_orders

class TestRiskManagement(unittest.TestCase):

    @patch('bybit_spot_analysis.client.Order.Order_new')
    def test_create_order(self, mock_order):
        # Подготовка мок-объекта
        mock_order.return_value = {"result": "success"}

        # Пример теста для создания ордера
        response = create_order('BTCUSD', 'Buy', 'Limit', 50000, 1, stop_loss=49000, take_profit=51000)
        self.assertEqual(response['result'], 'success')

    @patch('bybit_spot_analysis.client.Order.Order_cancelAll')
    def test_cancel_all_orders(self, mock_cancel):
        # Подготовка мок-объекта
        mock_cancel.return_value = {"result": "success"}

        # Пример теста для отмены ордеров
        response = cancel_all_orders('BTCUSD')
        self.assertEqual(response['result'], 'success')

    @patch('bybit_spot_analysis.create_order')
    def test_handle_risk_management(self, mock_create_order):
        # Мокируем создание ордера
        mock_create_order.return_value = {"result": "success"}

        # Тестируем управление рисками
        signal = {
            'BTCUSD': {
                'current_price': 50500,
                'stop_loss': 49000,
                'take_profit': 51000,
                'last_price': 50000,
                'qty': 1
            }
        }

        handle_risk_management(signal)
        mock_create_order.assert_called_with('BTCUSD', 'Sell', 'Market', None, 1, stop_loss=49000)

if __name__ == '__main__':
    unittest.main()
