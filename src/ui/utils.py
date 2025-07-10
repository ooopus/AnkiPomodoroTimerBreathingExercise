from aqt.qt import QScreen


def get_screen_identifier(screen: QScreen) -> str:
    """获取屏幕的唯一标识符，优先使用序列号，否则创建备用指纹"""
    serial = screen.serialNumber()
    if serial:
        return serial

    # 创建备用指纹
    manufacturer = screen.manufacturer()
    model = screen.model()
    res = screen.size()
    return f"{manufacturer}-{model}-{res.width()}x{res.height()}"
