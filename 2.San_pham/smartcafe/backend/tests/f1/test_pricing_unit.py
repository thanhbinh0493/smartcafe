"""F1 – Quy tắc chọn giá khuyến mãi (đơn vị, không cần CSDL)."""
import pytest

from app.modules.menu.service import apply_promo


@pytest.mark.parametrize("regular,promo,pid,expected", [
    (45000, None, None, (45000, None)),   # không có KM
    (45000, 36000, 7, (36000, 7)),        # KM rẻ hơn -> áp dụng
    (45000, 45000, 7, (45000, None)),     # KM bằng giá thường -> không coi là KM
    (27000, 29000, 7, (27000, None)),     # giá chi nhánh đã rẻ hơn giá KM -> giữ giá chi nhánh
    (45000, 0, 7, (0, 7)),                # KM tặng 0đ vẫn hợp lệ
])
def test_F1_06_apply_promo(regular, promo, pid, expected):
    assert apply_promo(regular, promo, pid) == expected
