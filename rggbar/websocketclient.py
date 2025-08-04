import json

from websocket import create_connection


class WebsocketClient:
    def __init__(self, host, port):
        self.url = "ws://{}:{}/ws".format(host, port)

    def send(self, data):
        try:
            ws = create_connection(self.url)
            ws.send(json.dumps(data))
            ws.close()
        except Exception as e:
            pass
