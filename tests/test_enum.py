import ctypes

def test_enum():
    hwnd_list = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def enum_cb(hwnd, _):
        if ctypes.windll.user32.IsWindowVisible(hwnd):
            length = ctypes.windll.user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buf = ctypes.create_unicode_buffer(length + 1)
                ctypes.windll.user32.GetWindowTextW(hwnd, buf, length + 1)
                title = buf.value.lower()
                hwnd_list.append((hwnd, title))
        return True
    
    print("Testing directly... Will it crash?")
    ctypes.windll.user32.EnumWindows(WNDENUMPROC(enum_cb), 0)
    print("Survival! Found", len(hwnd_list), "windows.")
    return hwnd_list

if __name__ == "__main__":
    test_enum()
