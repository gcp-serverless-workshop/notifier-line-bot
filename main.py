import base64
import json
import logging
import os
import sys

if os.getenv('API_ENV') != 'production':
    from dotenv import load_dotenv

    load_dotenv()


from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware

from linebot.v3.webhook import WebhookParser
from linebot.v3.messaging import (
    AsyncApiClient,
    AsyncMessagingApi,
    Configuration,
    ReplyMessageRequest,
    PushMessageRequest,
    TextMessage,
    FlexMessage
)
from linebot.v3.exceptions import (
    InvalidSignatureError
)
from linebot.v3.messaging import FlexContainer
from linebot.v3.webhooks import (
    MessageEvent,
    TextMessageContent,
)

import uvicorn

logging.basicConfig(level=os.getenv('LOG', 'WARNING'))
logger = logging.getLogger(__file__)

app = FastAPI()

# TODO: check CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

configuration = Configuration(
    access_token=channel_access_token
)

async_api_client = AsyncApiClient(configuration)
line_bot_api = AsyncMessagingApi(async_api_client)
parser = WebhookParser(channel_secret)


def order_flex(
    title,
    place,
    time,
    website,
    image_url="https://scdn.line-apps.com/n/channel_devcenter/img/fx/01_1_cafe.png",
):
    return {
        "type": "bubble",
        "hero": {
            "type": "image",
            "url": image_url,
            "size": "full",
            "aspectRatio": "20:13",
            "aspectMode": "cover",
            "action": {
                "type": "uri",
                "uri": "http://linecorp.com/"
            }
        },
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "xl"
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "margin": "lg",
                    "spacing": "sm",
                    "contents": [
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "Place",
                                    "color": "#aaaaaa",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": place,
                                    "wrap": True,
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 5
                                }
                            ]
                        },
                        {
                            "type": "box",
                            "layout": "baseline",
                            "spacing": "sm",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "Time",
                                    "color": "#aaaaaa",
                                    "size": "sm",
                                    "flex": 1
                                },
                                {
                                    "type": "text",
                                    "text": time,
                                    "wrap": True,
                                    "color": "#666666",
                                    "size": "sm",
                                    "flex": 5
                                }
                            ]
                        }
                    ]
                }
            ]
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "link",
                    "height": "sm",
                    "action": {
                        "type": "uri",
                        "label": "WEBSITE",
                        "uri": website
                    }
                },
                {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [],
                    "margin": "sm"
                }
            ],
            "flex": 0
        }
    }




@app.post('/sub')
async def publisher(request: Request):
    # pub: {"order_id": 22, "name":"居西批全家優惠碼"}
    body = await request.body()
    body = json.loads(body.decode())
    logger.info(f"Publisher original data is: {str(body)}")
    data = body.get('message').get('data')
    logger.info(f"Publisher content data is: {str(data)}")
    if data is None:
        return None
    else:
        data = json.loads(base64.b64decode(data))
        logger.info(f"Publisher data format struct: {str(data)}")
    
    if data.get('order_id') != None:
        order_json = order_flex(
            title=data.get('name'),
            place="JCConf",
            time="10:00~11:00",
            website="https://jcconf.tw/2023/"
        )
        message = FlexMessage(alt_text="hello", contents=FlexContainer.from_dict(order_json))
        await line_bot_api.push_message(push_message_request=PushMessageRequest(
                to=os.getenv('LINE_GROUP_ID'),
                messages=[message],
            ))


@app.post("/webhooks/line")
async def handle_callback(request: Request):
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = await request.body()
    body = body.decode()
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        raise HTTPException(status_code=400, detail="Invalid signature")

    for event in events:
        logging.info(event)
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessageContent):
            continue
        text = event.message.text
        source = event.source
        await line_bot_api.reply_message(
            ReplyMessageRequest(
                reply_token=event.reply_token,
                messages=[TextMessage(text=str(source))]
            ))
    return 'OK'


if __name__ == "__main__":
    port = int(os.environ.get('PORT', default=8000))
    debug = True if os.environ.get(
        'API_ENV', default='develop') == 'develop' else False
    logging.info('Application will start...')
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug)
