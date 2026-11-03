"""Chuẩn hóa và che số điện thoại di động Việt Nam (UC02)."""
import re

# Đầu số di động VN (10 số): 03x, 05x, 07x, 08x, 09x
_MOBILE = re.compile(r"^0[35789]\d{8}$")
_SEPARATORS = re.compile(r"[\s.\-()]")


def normalize_phone(raw: str) -> str | None:
    """Trả SĐT dạng 0xxxxxxxxx; None nếu không phải SĐT di động VN hợp lệ.

    Chấp nhận dấu cách, chấm, gạch nối và tiền tố +84 / 84.
    """
    s = _SEPARATORS.sub("", raw or "")
    if s.startswith("+84"):
        s = "0" + s[3:]
    elif s.startswith("84") and len(s) == 11:
        s = "0" + s[2:]
    return s if _MOBILE.match(s) else None


def mask_phone(phone: str) -> str:
    """0912345678 -> 0912 *** 678 (hiển thị trên W00a / W01)."""
    return f"{phone[:4]} *** {phone[-3:]}" if len(phone) >= 7 else "***"
