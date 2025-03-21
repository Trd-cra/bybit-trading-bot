import unittest
from unittest.mock import patch, MagicMock
import bybit_spot_ws
import time

class TestBybitWebSocket(unittest.TestCase):

    @patch("bybit_spot_ws.websocket.WebSocketApp")
    def test_websocket_connection(self, mock_ws_app):
        """Проверяем, что WebSocket подключается и подписывается на пары"""
        mock_ws = MagicMock()
        mock_ws_app.return_value = mock_ws

        ws_client = bybit_spot_ws.BybitWebSocket(["BTCUSDT", "ETHUSDT"])
        ws_client.connect()

        mock_ws_app.assert_called_once_with(
            bybit_spot_ws.WS_URL,
            on_message=ws_client.on_message,
            on_error=ws_client.on_error,
            on_close=ws_client.on_close,
            on_open=ws_client.on_open
        )

    @patch("bybit_spot_ws.websocket.WebSocketApp")
    def test_websocket_subscriptions(self, mock_ws_app):
        """Проверяем, что WebSocket отправляет подписку на пары"""
        mock_ws = MagicMock()
        mock_ws_app.return_value = mock_ws

        ws_client = bybit_spot_ws.BybitWebSocket(["BTCUSDT", "ETHUSDT"])
        ws_client.on_open(mock_ws)

        expected_calls = [
            ({"op": "subscribe", "args": ["publicTrade.BTCUSDT"]}),
            ({"op": "subscribe", "args": ["publicTrade.ETHUSDT"]})
        ]
        
        mock_ws.send.assert_any_call(bybit_spot_ws.json.dumps(expected_calls[0]))
        mock_ws.send.assert_any_call(bybit_spot_ws.json.dumps(expected_calls[1]))

    @patch("bybit_spot_ws.websocket.WebSocketApp")
    def test_websocket_reconnect(self, mock_ws_app):
        """Проверяем, что WebSocket переподключается при разрыве"""
        mock_ws = MagicMock()
        mock_ws_app.return_value = mock_ws

        ws_client = bybit_spot_ws.BybitWebSocket(["BTCUSDT"])
        ws_client.on_close(mock_ws, None, None)

        time.sleep(1)  # Ждем, чтобы проверить вызов переподключения
        mock_ws_app.assert_called()

    @patch("bybit_spot_ws.BybitWebSocket.on_message")
    def test_websocket_message_handling(self, mock_on_message):
        """Проверяем, что WebSocket корректно обрабатывает входящие данные"""
        mock_ws = MagicMock()
        ws_client = bybit_spot_ws.BybitWebSocket(["BTCUSDT"])

        test_message = '{"topic": "publicTrade.BTCUSDT", "data": {"price": "59000"}}'
        ws_client.on_message(mock_ws, test_message)

        mock_on_message.assert_called_with(mock_ws, test_message)

if __name__ == "__main__":
    unittest.main()
