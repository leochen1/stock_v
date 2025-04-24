from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import MessageEvent, TextMessage

app = Flask(__name__)

YOUR_CHANNEL_ACCESS_TOKEN = 'aR3GEe7B4hzK58ir/halgz4d58ZArkeXBa5XXK6BBBvIgqkgCq7unGsRK3r1nHK8a9qHQTGynl2QDrcJ+CqAov/iafn6ic9rldDQMkKuRZocElxMRK3wcju7Bp8lEnRo8CHr448jEqZDI97ovWJS4gdB04t89/1O/w1cDnyilFU='
YOUR_CHANNEL_SECRET = 'ae8e533d679b2ff7920f452db407060d'

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)
handler = WebhookHandler(YOUR_CHANNEL_SECRET)

@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    try:
        handler.handle(body, signature)
    except Exception as e:
        abort(400)
    return 'OK'

@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    user_id = event.source.user_id
    print(f"收到訊息的 User ID：{user_id}")
    # 你可以把 user_id 存到資料庫或檔案

if __name__ == "__main__":
    app.run(port=3333)