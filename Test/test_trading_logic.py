import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_analysis

class TestTradingLogic(unittest.TestCase):

    @patch("bybit_spot_analysis.create_order")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_buy_signal_execution(self, mock_get_open_orders, mock_create_order):
        """Проверяем, что бот открывает ордер на покупку при сильном сигнале"""
        mock_get_open_orders.return_value = []  # Нет открытых ордеров
        mock_create_order.return_value = "12345"  # Возвращаем фиктивный orderId

        buy_signal = {"BTCUSDT": True}  # Сильный сигнал на покупку
        bybit_spot_analysis.handle_trading_logic(buy_signal)

        mock_create_order.assert_called_once_with("BTCUSDT", "Buy", "Market", None, "0.1")

    @patch("bybit_spot_analysis.create_order")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_no_duplicate_buy_orders(self, mock_get_open_orders, mock_create_order):
        """Проверяем, что бот не открывает новый ордер, если уже есть открытый"""
        mock_get_open_orders.return_value = [{"orderId": "12345", "symbol": "BTCUSDT", "side": "Buy"}]

        buy_signal = {"BTCUSDT": True}  # Повторный сигнал на покупку
        bybit_spot_analysis.handle_trading_logic(buy_signal)

        mock_create_order.assert_not_called()  # Новый ордер не должен создаваться

    @patch("bybit_spot_analysis.cancel_all_orders")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_sell_signal_execution(self, mock_get_open_orders, mock_cancel_all_orders):
        """Проверяем, что бот закрывает ордер при сигнале на продажу"""
        mock_get_open_orders.return_value = [{"orderId": "12345", "symbol": "BTCUSDT", "side": "Buy"}]

        sell_signal = {"BTCUSDT": False}  # ❗ Теперь False = сигнал на продажу (исправлено!)
        bybit_spot_analysis.handle_trading_logic(sell_signal)

        mock_cancel_all_orders.assert_called_once()  # Должен сработать стоп

    @patch("bybit_spot_analysis.create_order")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_no_order_on_weak_signal(self, mock_get_open_orders, mock_create_order):
        """Проверяем, что бот игнорирует слабые сигналы"""
        mock_get_open_orders.return_value = []  # Нет открытых ордеров

        weak_signal = {"BTCUSDT": False}  # ❗ Теперь False = слабый сигнал
        bybit_spot_analysis.handle_trading_logic(weak_signal)

        mock_create_order.assert_not_called()  # Бот не должен открывать ордер

    @patch("bybit_spot_analysis.cancel_all_orders")
    @patch("bybit_spot_analysis.create_order")
    @patch("bybit_spot_analysis.get_open_orders")
    def test_full_trade_cycle(self, mock_get_open_orders, mock_create_order, mock_cancel_all_orders):
        """Проверяем полный цикл торговли: покупка -> продажа"""
        # 1. Сначала нет ордеров → должен открыться
        mock_get_open_orders.return_value = []
        mock_create_order.return_value = "12345"

        buy_signal = {"BTCUSDT": True}
        bybit_spot_analysis.handle_trading_logic(buy_signal)
        mock_create_order.assert_called_once_with("BTCUSDT", "Buy", "Market", None, "0.1")

        # 2. Потом появляется открытая позиция → сигнал на продажу
        mock_get_open_orders.return_value = [{"orderId": "12345", "symbol": "BTCUSDT", "side": "Buy"}]

        sell_signal = {"BTCUSDT": False}  # Выход из сделки
        bybit_spot_analysis.handle_trading_logic(sell_signal)

        mock_cancel_all_orders.assert_called_once()  # Проверяем, что отменяется ордер

if __name__ == "__main__":
    unittest.main()
