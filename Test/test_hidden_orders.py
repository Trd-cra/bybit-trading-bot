import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_analysis

class TestHiddenOrders(unittest.TestCase):

    @patch("bybit_spot_analysis.create_hidden_order")
    def test_hidden_limit_order(self, mock_create_hidden_order):
        """🕵️‍♂️ Проверяем отправку скрытого лимитного ордера"""
        test_signal = {
            "BTCUSDT": {
                "price": 47000,
                "qty": 0.5,
                "hidden": True,  # Скрытый ордер
            }
        }

        bybit_spot_analysis.handle_hidden_order(test_signal)

        mock_create_hidden_order.assert_called_once_with("BTCUSDT", "Buy", 47000, 0.5)

    @patch("bybit_spot_analysis.create_iceberg_order")
    def test_iceberg_order(self, mock_create_iceberg_order):
        """❄️ Проверяем отправку Iceberg-ордера (разделение большого объема)"""
        test_signal = {
            "BTCUSDT": {
                "price": 47000,
                "qty": 5,  # Крупный объем
                "iceberg": True,  # Iceberg-режим
                "visible_qty": 1  # Видимая часть 1 BTC
            }
        }

        bybit_spot_analysis.handle_hidden_order(test_signal)

        mock_create_iceberg_order.assert_called_once_with("BTCUSDT", "Buy", 47000, 5, 1)

if __name__ == "__main__":
    unittest.main()
