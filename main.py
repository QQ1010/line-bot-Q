from __future__ import unicode_literals
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, TemplateSendMessage, ButtonsTemplate, MessageTemplateAction, PostbackEvent, PostbackTemplateAction, PostbackAction
import configparser
import requests
import json

app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('linebot', 'channel_access_token'))
handler = WebhookHandler(config.get('linebot', 'channel_secret'))


# 接收 LINE 的資訊
@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        print(
            "Invalid signature. Please check your channel access token/channel secret."
        )
        abort(400)

    return 'OK'


# 設定回復
@handler.add(MessageEvent, message=TextMessage)
def handle_weahter_message(event):
    if isinstance(event, MessageEvent):
        print("message event")
        if event.message.text == "天氣":
            line_bot_api.reply_message(  # 回復傳入的訊息文字
                event.reply_token,
                TemplateSendMessage(alt_text='Buttons template',
                                    template=ButtonsTemplate(
                                        title='查詢天氣地點',
                                        text='請選擇地區',
                                        actions=[
                                            PostbackAction(label='臺北市',
                                                           data='臺北市'),
                                            PostbackAction(label='彰化縣',
                                                           data='彰化縣'),
                                        ])))
        else:
            line_bot_api.reply_message(event.reply_token,
                                   TextSendMessage(text=event.message.text))


@handler.add(PostbackEvent)
def handle_weather_postback(event):
    weather = reply_weather(event.postback.data)
    line_bot_api.reply_message(event.reply_token,
                               TextSendMessage(text=weather))


def reply_weather(location_name):
    request_URL = "https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001"
    params = {
        "Authorization": config.get('weather', 'access_token'),
        "locationName": location_name,
    }
    response = requests.get(request_URL, params=params)
    if (response.status_code == 200):
        data = json.loads(response.text)
        # print(data["records"])
        location = data["records"]["location"][0]["locationName"]
        weather_elements = data["records"]["location"][0]["weatherElement"]
        # start_time = weather_elements[0]["time"][0]["startTime"]
        # end_time = weather_elements[0]["time"][0]["endTime"]
        weather_state = weather_elements[0]["time"][0]["parameter"][
            "parameterName"]
        rain_prob = weather_elements[1]["time"][0]["parameter"][
            "parameterName"]
        min_tem = weather_elements[2]["time"][0]["parameter"]["parameterName"]
        comfort = weather_elements[3]["time"][0]["parameter"]["parameterName"]
        max_tem = weather_elements[4]["time"][0]["parameter"]["parameterName"]
        weather_result = "地點🌏： " + location + "\n今日天氣狀況⛅： " + weather_state + "\n今日降雨機率☔： " + rain_prob + "\n最高溫度： " + max_tem + "\n最低溫度： " + min_tem + "\n體感溫度狀況： " + comfort
        return weather_result
    else:
        print("Can't get data.")
        return "Can't get weather data"


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8080)
