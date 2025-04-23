from linebot import LineBotApi
from linebot.models import TextSendMessage
from linebot.exceptions import LineBotApiError

# 替換成你的 Channel access token
YOUR_CHANNEL_ACCESS_TOKEN = 'aR3GEe7B4hzK58ir/halgz4d58ZArkeXBa5XXK6BBBvIgqkgCq7unGsRK3r1nHK8a9qHQTGynl2QDrcJ+CqAov/iafn6ic9rldDQMkKuRZocElxMRK3wcju7Bp8lEnRo8CHr448jEqZDI97ovWJS4gdB04t89/1O/w1cDnyilFU='

# 替換成接收訊息的 User ID、Group ID 或 Room ID
# 你需要先取得這個 ID，例如透過 Webhook 事件或 LINE Developers 文件說明的方法
TARGET_ID = 'Ue29e2eb096538c363367923715c6d0da'

line_bot_api = LineBotApi(YOUR_CHANNEL_ACCESS_TOKEN)

def send_text_message(target_id, message):
    """
    向指定的目標 ID 發送文字訊息。

    Args:
        target_id (str): 接收訊息的 User ID、Group ID 或 Room ID。
        message (str): 要發送的文字內容。
    """
    try:
        line_bot_api.push_message(
            target_id,
            TextSendMessage(text=message)
        )
        print(f"成功向 {target_id} 發送訊息: {message}")
    except LineBotApiError as e:
        print(f"發送訊息失敗: {e}")

if __name__ == '__main__':
    message_to_send = "這是一個測試訊息！"
    send_text_message(TARGET_ID, message_to_send)