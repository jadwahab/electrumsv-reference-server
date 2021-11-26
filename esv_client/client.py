import asyncio
import json
import logging
import sys

import traceback
import aiohttp
import bitcoinx
from aiohttp import ClientConnectorError, web
from aiohttp.web_exceptions import HTTPClientError

from esv_reference_server.errors import Error

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 47124
BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
WS_URL_HEADERS = "http://localhost:47124/api/v1/headers/websocket"
WS_URL_TEMPLATE_MSG_BOX = "http://localhost:47124/api/v1/channel/{channelid}/notify"


class MockApplicationState:

    def __init__(self) -> None:
        # some state
        pass


class ElectrumSVClient:
    def __init__(self, app_state: MockApplicationState) -> None:
        self.app_state = app_state
        self.logger = logging.getLogger("electrumsv-client")

    async def subscribe_to_headers_notifications(self) -> None:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL_HEADERS, timeout=5.0) as ws:
                print(f'Connected to {WS_URL_HEADERS}')

                async for msg in ws:
                    new_tip_hash = bitcoinx.hash_to_hex_str(bitcoinx.double_sha256(msg.data[0:80]))
                    new_tip_height = bitcoinx.unpack_be_uint32(msg.data[80:84])[0]
                    print('Message new chain tip hash: ', new_tip_hash, 'height: ', new_tip_height)
                    if msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        break

    async def subscribe_to_msg_box_notifications(self, url: str, msg_box_api_token: str) -> None:
        async with aiohttp.ClientSession() as session:
            headers = {"Authorization": f"Bearer {msg_box_api_token}"}
            async with session.ws_connect(url, headers=headers, timeout=5.0) as ws:
                print(f'Connected to {url}')

                async for msg in ws:
                    msg: aiohttp.WSMessage
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        content = json.loads(msg.data)
                        print('New message from msg box: ', content)
                        if content.get('error'):
                            error: Error = Error.from_websocket_dict(content)
                            print(f"Websocket error: {error}")
                            if error.status == web.HTTPUnauthorized.status_code:
                                raise web.HTTPUnauthorized()

                    if msg.type in (aiohttp.WSMsgType.CLOSE, aiohttp.WSMsgType.ERROR,
                            aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.CLOSING):
                        print("CLOSED")
                        break


# entrypoint to main event loop
async def main() -> None:
    app_state = MockApplicationState()
    client = ElectrumSVClient(app_state)
    msg_box_external_id = "HAECY_dKwCam1BexdRjYBklWBICXWTPud0IgqnDq7rwJRYAWl86X9fWJSuo528q1aZ34xs1TtImpP0mrUprerA=="
    msg_box_api_token = "MkAmn-DSMbXfKAlglTrl_-_Cjc77J0yzbamUcGQYcGRDBfK0O1i3vCZoK-iMo9-mbEONGWM6thx3RYlkAC237w=="
    url = WS_URL_TEMPLATE_MSG_BOX.format(channelid=msg_box_external_id)
    while True:
        try:
            # await client.subscribe_to_headers_notifications()  # using aiohttp
            await client.subscribe_to_msg_box_notifications(url, msg_box_api_token)  # using aiohttp
        except HTTPClientError as e:
            break
        except (ConnectionRefusedError, ClientConnectorError):
            # print(f"Unable to connect to: {WS_URL_HEADERS} - retrying...")
            print(f"Unable to connect to: {url} - retrying...")
        except Exception as e:
            exc_type, exc_value, exc_tb = sys.exc_info()
            tb = traceback.TracebackException(exc_type, exc_value, exc_tb)
            print(''.join(tb.format_exception_only()))
            break


if __name__ == "__main__":
    asyncio.run(main())
