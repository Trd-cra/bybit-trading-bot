import asyncio
import websockets
import json

# URL WebSocket API Bybit (Testnet)
WS_URL = "wss://stream-testnet.bybit.com/v5/public/spot"

async def subscribe_ticker():
    async with websockets.connect(WS_URL) as ws:
        # Подписка на обновления цены BTC/USDT
        subscribe_msg = {
            "op": "subscribe",
            "args": ["tickers.BTCUSDT"]
        }
        await ws.send(json.dumps(subscribe_msg))
        print("✅ Подключено к WebSocket, подписка отправлена!")

        while True:
            response = await ws.recv()
            print("📊 Данные от Bybit:", response)

asyncio.run(subscribe_ticker())
