import pyautogui
import time

def keep_awake(interval_seconds=3):
    print("🟢 Keep Awake script started. Press Ctrl+C to stop.")
    while True:
        pyautogui.moveRel(100, 0, duration=2)  # 往右移動 100 像素
        pyautogui.click()                      # 點擊滑鼠左鍵
        pyautogui.moveRel(-100, 0, duration=2) # 再移回來
        print(f"✅ Moved mouse at {time.strftime('%Y-%m-%d %H:%M:%S')}")
        time.sleep(interval_seconds)

if __name__ == "__main__":
    keep_awake(interval_seconds=3)  # 每 3 秒執行一次