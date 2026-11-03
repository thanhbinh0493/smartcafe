"""F7 – FP-Growth "Thường gọi kèm", job hằng đêm, gắn đơn vào log gợi ý, dữ liệu mẫu, đánh giá offline."""
import random
from datetime import timedelta

import pytest
from sqlalchemy import func, select

from app.models import AssociationRule, Customer, LoyaltyTransaction, Order, OrderItem, RecommendationLog
from app.modules.recommend import scheduler as sched_mod
from app.modules.recommend.training import MIN_TRANSACTIONS, mine_rules, rebuild_rules
from scripts.evaluate_recommender import evaluate
from scripts.seed_orders import DEMO_PHONE, Params, already_seeded, seed_orders
from tests import factories as f
from tests.f2.conftest import place
from tests.f7.conftest import NOW, member_auth, names, recs


# ---------- Khai phá luật ----------
def test_F7_23_fp_growth_tim_dung_cap_mon_hay_mua_cung():
    rng = random.Random(1)
    baskets = []
    for _ in range(200):
        b = {rng.choice([3, 4, 5, 6])}
        if 1 in b or rng.random() < 0.3:
            b.add(1)
        if 1 in b and rng.random() < 0.7:
            b.add(2)            # 1 → 2 rất mạnh
        baskets.append(b)
    rules = {(r.antecedent_id, r.consequent_id): r for r in mine_rules(baskets, 0.01, 0.2)}
    assert (1, 2) in rules and rules[(1, 2)].confidence >= 0.6 and rules[(1, 2)].lift > 1
    for r in rules.values():
        assert r.support >= 0.01 and r.confidence >= 0.2 and r.lift > 1 and r.antecedent_id != r.consequent_id


def test_F7_24_qua_it_don_hoac_khong_co_cap_thi_khong_hoc():
    assert mine_rules([{1, 2}] * (MIN_TRANSACTIONS - 1), 0.01, 0.2) == []
    assert mine_rules([{i % 5} for i in range(100)], 0.01, 0.2) == []           # mỗi đơn 1 món
    assert mine_rules([{1, 2}] * 50, 0.01, 0.2) == []                            # luôn đi cùng: lift = 1


def test_F7_25_hoc_lai_luat_theo_chi_nhanh_va_toan_chuoi(db, cafe):
    for i in range(30):
        cafe.sell(cafe.cg, (cafe.sua_da, 1), *([(cafe.croissant, 1)] if i % 3 else []), days_ago=1 + i % 20)
        cafe.sell(cafe.cg, (cafe.tra_dao if i % 2 else cafe.tra_gung, 1), days_ago=2)
    for i in range(25):                                                          # không tính: hủy / quá 60 ngày
        cafe.sell(cafe.cg, (cafe.bac_xiu, 1), (cafe.tra_gung, 1), days_ago=1, status="CANCELLED")
        cafe.sell(cafe.cg, (cafe.bac_xiu, 1), (cafe.tra_gung, 1), days_ago=70)
    db.add(AssociationRule(branch_id=None, antecedent_id=cafe.tra_dao.id, consequent_id=cafe.bac_xiu.id,
                           support=0.5, confidence=0.9, lift=2))                 # luật cũ bị thay
    db.flush()
    counts = rebuild_rules(db, NOW)
    rules = db.scalars(select(AssociationRule)).all()
    pairs = {(r.branch_id, r.antecedent_id, r.consequent_id) for r in rules}
    assert (cafe.cg.id, cafe.sua_da.id, cafe.croissant.id) in pairs and (None, cafe.sua_da.id, cafe.croissant.id) in pairs
    assert not any(r.antecedent_id == cafe.bac_xiu.id or r.consequent_id == cafe.bac_xiu.id for r in rules)
    assert counts == {"CG": counts["CG"], "ALL": counts["ALL"]} and counts["CG"] == len([r for r in rules if r.branch_id])


def test_F7_26_thuong_goi_kem_trong_gio_hang(client, db, cafe):
    def rule(branch, a, c, conf, lift):
        db.add(AssociationRule(branch_id=branch.id if branch else None, antecedent_id=a.id, consequent_id=c.id,
                               support=0.1, confidence=conf, lift=lift))

    rule(None, cafe.sua_da, cafe.croissant, 0.5, 2.0)        # 1,0
    rule(cafe.cg, cafe.sua_da, cafe.tra_dao, 0.3, 1.5)       # 0,45 nhưng là luật của chi nhánh → ưu tiên
    rule(None, cafe.sua_da, cafe.bac_xiu, 0.9, 3.0)          # Bạc xỉu tạm hết → bỏ
    rule(None, cafe.sua_da, cafe.tra_gung, 0.2, 1.1)         # thứ 4 → ngoài top 2
    rule(None, cafe.croissant, cafe.sua_da, 0.6, 2.0)        # món đã trong giỏ → bỏ
    rule(cafe.hd, cafe.sua_da, cafe.sua_nong, 0.9, 5.0)      # luật chi nhánh khác → bỏ
    f.branch_item(db, cafe.cg, cafe.bac_xiu, available=False)
    db.flush()
    r = recs(client, cafe.cg, cart=[cafe.sua_da])
    assert [(i["name"], i["reason"], i["reason_code"]) for i in r["also_bought"]] == [
        ("Trà đào cam sả", "Thường gọi kèm Cà phê sữa đá", "CO_BUY"),
        ("Bánh croissant", "Thường gọi kèm Cà phê sữa đá", "CO_BUY")]
    assert recs(client, cafe.cg)["also_bought"] == []
    assert names(recs(client, cafe.cg, cart=[cafe.sua_da, cafe.croissant])["also_bought"]) == ["Trà đào cam sả", "Trà gừng"]


def test_F7_27_job_hang_dem_00_30_gio_viet_nam(monkeypatch, _mock_weather):
    s = _mock_weather
    assert sched_mod.start_scheduler() is None                                    # tắt trong test
    s.scheduler_enabled = True
    try:
        sch = sched_mod.start_scheduler()
        job = sch.get_job("rebuild_rules")
        assert str(job.trigger.timezone) == "Asia/Ho_Chi_Minh"
        assert "hour='0'" in str(job.trigger) and "minute='30'" in str(job.trigger)
        sch.shutdown(wait=False)
    finally:
        s.scheduler_enabled = False

    def boom(db):
        raise RuntimeError("CSDL lỗi")
    monkeypatch.setattr(sched_mod, "rebuild_rules", boom)
    sched_mod.rules_job()                                                          # không ném lỗi ra ngoài


# ---------- Gắn đơn vào log gợi ý (D34) ----------
def test_F7_28_dat_don_kem_recommendation_log_id(client, db, cafe):
    r = recs(client, cafe.cg)
    body = {"qr_token": cafe.t_cg.qr_token, "recommendation_log_id": r["log_id"],
            "items": [{"menu_item_id": r["items"][0]["menu_item_id"], "quantity": 1, "is_recommended": True}]}
    o = client.post("/api/public/orders", json=body)
    assert o.status_code == 201
    log = db.get(RecommendationLog, r["log_id"])
    db.refresh(log)
    assert log.order_id == o.json()["order_id"]
    assert db.scalar(select(OrderItem.is_recommended).where(OrderItem.order_id == log.order_id)) is True
    # Dùng lại log đã gắn: đơn vẫn tạo được, log giữ đơn cũ
    o2 = client.post("/api/public/orders", json=body)
    assert o2.status_code == 201
    db.refresh(log)
    assert log.order_id == o.json()["order_id"]


@pytest.mark.parametrize("case", ["chi_nhanh_khac", "khach_khac", "khong_ton_tai", "qua_2_gio"])
def test_F7_29_log_khong_hop_le_thi_bo_qua_don_van_dat_duoc(client, db, cafe, case):
    headers = {}
    if case == "chi_nhanh_khac":
        log_id = recs(client, cafe.hd)["log_id"]
    elif case == "khach_khac":
        log_id = recs(client, cafe.cg, headers=member_auth(cafe.member))["log_id"]
    elif case == "qua_2_gio":
        log_id = recs(client, cafe.cg)["log_id"]
        db.get(RecommendationLog, log_id).created_at = NOW - timedelta(hours=3)
        db.flush()
    else:
        log_id = 999999
    body = {"qr_token": cafe.t_cg.qr_token, "recommendation_log_id": log_id,
            "items": [{"menu_item_id": cafe.sua_da.id, "quantity": 1}]}
    assert client.post("/api/public/orders", json=body, headers=headers).status_code == 201
    log = db.get(RecommendationLog, log_id)
    if log:
        db.refresh(log)
        assert log.order_id is None
    assert place(client, cafe.t_cg, (cafe.sua_da, 1), recommendation_log_id=0).status_code == 422


# ---------- Dữ liệu mẫu + đánh giá offline ----------
@pytest.fixture
def seeded(db):
    from scripts.seed_data import seed
    seed(db)
    counts = seed_orders(db, p=Params(days=14, orders_per_day=12, members=30))
    return counts


def test_F7_30_seed_orders_sinh_du_lieu_hop_le(db, seeded):
    assert seeded["customers"] == 30 and seeded["orders"] > 300 and seeded["rules"] > 0
    assert already_seeded(db)
    statuses = dict(db.execute(select(Order.status, func.count()).group_by(Order.status)).all())
    assert set(statuses) == {"COMPLETED", "CANCELLED"} and statuses["CANCELLED"] < statuses["COMPLETED"] * 0.1
    dup = db.execute(select(Order.order_code, Order.order_date).group_by(Order.order_code, Order.order_date)
                     .having(func.count() > 1)).all()
    assert dup == []
    # Điểm khách = tổng giao dịch EARN; mỗi đơn hoàn tất của thành viên có đúng 1 giao dịch
    for c in db.scalars(select(Customer)):
        assert c.loyalty_points == (db.scalar(select(func.sum(LoyaltyTransaction.points))
                                              .where(LoyaltyTransaction.customer_id == c.id)) or 0)
    demo = db.scalar(select(Customer).where(Customer.phone == DEMO_PHONE))
    assert db.scalar(select(func.count()).where(Order.customer_id == demo.id)) >= 3
    # Không có đơn chứa món mới tạo sau ngày đơn
    from app.models import MenuItem
    bad = db.scalar(select(func.count()).select_from(OrderItem).join(Order).join(MenuItem)
                    .where(MenuItem.created_at > Order.paid_at))
    assert bad == 0
    # Quy luật cài sẵn được học lại: Cà phê sữa đá → Bánh croissant bơ
    names_by_id = dict(db.execute(select(MenuItem.id, MenuItem.name)).all())
    pairs = {(names_by_id[r.antecedent_id], names_by_id[r.consequent_id]) for r in db.scalars(select(AssociationRule))}
    assert ("Cà phê sữa đá", "Bánh croissant bơ") in pairs


def test_F7_31_danh_gia_offline_thanh_vien_hon_baseline(db, seeded):
    rep = evaluate(db, limit=150, seed=3)
    s = rep.scores
    assert rep.test_orders > 0 and rep.rules > 0
    member = s["THÀNH VIÊN (đơn thành viên)"]
    assert member.total > 10
    assert member.rate > s["POPULAR (đơn thành viên)"].rate                     # cá nhân hóa có ích
