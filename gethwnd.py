import win32gui

# 通过窗口标题获取 hWnd
hWnd = win32gui.FindWindow(None, "poi")  # 第二个参数是窗口标题

if hWnd:
    print(f"找到窗口 HWND: {hex(hWnd)}")
else:
    print("未找到窗口")
