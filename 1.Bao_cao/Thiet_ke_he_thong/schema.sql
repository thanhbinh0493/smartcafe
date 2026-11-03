-- =====================================================================
-- CSDL: coffee_chain (PostgreSQL 16)
-- Dự án: Phần mềm quản lý chuỗi quán cà phê thông minh - Nhóm 8
-- Mục IV.1 - Thiết kế CSDL (Relational Schema)
-- Quy ước: tiền tệ lưu INT (đơn vị VND), thời gian lưu TIMESTAMPTZ (UTC)
-- =====================================================================

-- ---------- Kiểu liệt kê ----------
CREATE TYPE staff_role     AS ENUM ('ADMIN', 'MANAGER', 'CASHIER', 'BARISTA');
CREATE TYPE temp_type      AS ENUM ('HOT', 'COLD', 'BOTH', 'NONE');
CREATE TYPE order_status   AS ENUM ('PENDING_PAYMENT', 'PAID', 'PREPARING', 'READY', 'COMPLETED', 'CANCELLED');
CREATE TYPE item_status    AS ENUM ('WAITING', 'PREPARING', 'DONE', 'CANCELLED');
CREATE TYPE change_source  AS ENUM ('CUSTOMER', 'STAFF', 'SYSTEM');
CREATE TYPE payment_method AS ENUM ('MOCK_EWALLET', 'MOCK_CARD');
CREATE TYPE payment_status AS ENUM ('SUCCESS', 'FAILED', 'REFUNDED');
CREATE TYPE loyalty_type   AS ENUM ('EARN', 'ADJUST');                 -- chưa có REDEEM (không làm đổi điểm)
CREATE TYPE rec_mode       AS ENUM ('ANONYMOUS', 'MEMBER');

-- ---------- Chi nhánh & nhân viên ----------
CREATE TABLE branches (
    id          SERIAL PRIMARY KEY,
    code        VARCHAR(20)  NOT NULL UNIQUE,          -- VD: CG (Cầu Giấy), dùng làm tiền tố mã đơn
    name        VARCHAR(100) NOT NULL,
    address     VARCHAR(255) NOT NULL,
    phone       VARCHAR(15),
    latitude    NUMERIC(9,6),                           -- dùng gọi Weather API
    longitude   NUMERIC(9,6),
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE TABLE staff (
    id             SERIAL PRIMARY KEY,
    branch_id      INT REFERENCES branches(id),         -- NULL với ADMIN (trụ sở)
    full_name      VARCHAR(100) NOT NULL,
    username       VARCHAR(50)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,               -- bcrypt
    role           staff_role   NOT NULL,
    phone          VARCHAR(15),
    is_active      BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT chk_staff_branch CHECK (
        (role = 'ADMIN' AND branch_id IS NULL) OR (role <> 'ADMIN' AND branch_id IS NOT NULL)
    )
);

-- ---------- Thực đơn ----------
CREATE TABLE categories (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(50) NOT NULL UNIQUE,
    sort_order  INT         NOT NULL DEFAULT 0,
    is_active   BOOLEAN     NOT NULL DEFAULT TRUE
);

CREATE TABLE menu_items (
    id                SERIAL PRIMARY KEY,
    category_id       INT          NOT NULL REFERENCES categories(id),
    name              VARCHAR(100) NOT NULL,
    description       TEXT,
    base_price        INT          NOT NULL CHECK (base_price >= 0),
    image_url         VARCHAR(255),
    temperature_type  temp_type    NOT NULL DEFAULT 'BOTH',   -- dùng cho gợi ý theo thời tiết
    tags              TEXT[]       NOT NULL DEFAULT '{}',     -- VD: {coffee, sweet, milk}
    is_active         BOOLEAN      NOT NULL DEFAULT TRUE,     -- ngừng bán toàn chuỗi
    is_deleted        BOOLEAN      NOT NULL DEFAULT FALSE,    -- xóa mềm để giữ lịch sử đơn
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_menu_items_category ON menu_items(category_id) WHERE is_deleted = FALSE;

-- Menu chung + tùy biến theo chi nhánh.
-- Không có dòng nào = chi nhánh bán món với giá chung, còn hàng.
CREATE TABLE branch_menu_items (
    branch_id       INT         NOT NULL REFERENCES branches(id),
    menu_item_id    INT         NOT NULL REFERENCES menu_items(id),
    price_override  INT         CHECK (price_override >= 0),  -- NULL = dùng base_price
    is_available    BOOLEAN     NOT NULL DEFAULT TRUE,        -- FALSE = "Tạm hết"
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (branch_id, menu_item_id)
);

-- ---------- Khuyến mãi ----------
-- Có hiệu lực khi is_active AND now() BETWEEN start_at AND end_at.
-- Nếu nhiều chương trình cùng áp dụng cho 1 món thì lấy giá thấp nhất.
CREATE TABLE promotions (
    id           SERIAL PRIMARY KEY,
    name         VARCHAR(100) NOT NULL,
    description  VARCHAR(255),
    branch_id    INT          REFERENCES branches(id),   -- NULL = toàn chuỗi
    start_at     TIMESTAMPTZ  NOT NULL,
    end_at       TIMESTAMPTZ  NOT NULL,
    is_active    BOOLEAN      NOT NULL DEFAULT TRUE,
    created_by   INT          NOT NULL REFERENCES staff(id),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CHECK (end_at > start_at)
);
CREATE INDEX idx_promotions_active ON promotions(branch_id, start_at, end_at) WHERE is_active;

CREATE TABLE promotion_items (
    promotion_id  INT NOT NULL REFERENCES promotions(id) ON DELETE CASCADE,
    menu_item_id  INT NOT NULL REFERENCES menu_items(id),
    promo_price   INT NOT NULL CHECK (promo_price >= 0),
    PRIMARY KEY (promotion_id, menu_item_id)
);

-- ---------- Bàn & khách hàng ----------
CREATE TABLE dining_tables (
    id            SERIAL PRIMARY KEY,
    branch_id     INT         NOT NULL REFERENCES branches(id),
    table_number  VARCHAR(10) NOT NULL,
    qr_token      VARCHAR(32) NOT NULL UNIQUE,   -- chuỗi ngẫu nhiên (secrets.token_urlsafe), in vào QR
    is_active     BOOLEAN     NOT NULL DEFAULT TRUE,
    UNIQUE (branch_id, table_number)
);

-- Khách thành viên: chỉ được tạo sau khi xác thực OTP thành công.
CREATE TABLE customers (
    id                SERIAL PRIMARY KEY,
    phone             VARCHAR(15)  NOT NULL UNIQUE,   -- định danh duy nhất, không thu thập tên (D31)
    loyalty_points    INT          NOT NULL DEFAULT 0 CHECK (loyalty_points >= 0),  -- = SUM(loyalty_transactions.points)
    created_at        TIMESTAMPTZ  NOT NULL DEFAULT now(),
    last_verified_at  TIMESTAMPTZ
);

-- OTP giả lập: mã 6 số, lưu dạng băm, hết hạn sau 5 phút, tối đa 5 lần nhập sai.
CREATE TABLE otp_requests (
    id           BIGSERIAL PRIMARY KEY,
    phone        VARCHAR(15)  NOT NULL,
    code_hash    VARCHAR(255) NOT NULL,
    attempts     SMALLINT     NOT NULL DEFAULT 0,
    expires_at   TIMESTAMPTZ  NOT NULL,
    verified_at  TIMESTAMPTZ,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_otp_phone ON otp_requests(phone, created_at DESC);

-- ---------- Đơn hàng ----------
CREATE TABLE orders (
    id             BIGSERIAL PRIMARY KEY,
    order_code     VARCHAR(20)  NOT NULL,            -- VD: CG-0142 (số thứ tự trong ngày, đếm lại mỗi ngày)
    order_date     DATE         NOT NULL DEFAULT ((now() AT TIME ZONE 'Asia/Ho_Chi_Minh')::date),  -- ngày tạo đơn (giờ VN)
    access_token   VARCHAR(32)  NOT NULL UNIQUE,     -- token ngẫu nhiên cho trang theo dõi đơn của khách
    branch_id      INT          NOT NULL REFERENCES branches(id),
    table_id       INT          NOT NULL REFERENCES dining_tables(id),
    customer_id    INT          REFERENCES customers(id),
    status         order_status NOT NULL DEFAULT 'PENDING_PAYMENT',
    total_amount   INT          NOT NULL CHECK (total_amount >= 0),
    note           VARCHAR(255),
    cancel_reason  VARCHAR(255),
    cancelled_by   INT          REFERENCES staff(id),
    completed_by   INT          REFERENCES staff(id),
    created_at     TIMESTAMPTZ  NOT NULL DEFAULT now(),
    paid_at        TIMESTAMPTZ,
    ready_at       TIMESTAMPTZ,
    completed_at   TIMESTAMPTZ,
    cancelled_at   TIMESTAMPTZ,
    CONSTRAINT uq_orders_code_date UNIQUE (order_code, order_date)   -- mã đơn không trùng trong cùng 1 ngày (D28)
);
CREATE INDEX idx_orders_branch_date    ON orders(branch_id, order_date);
CREATE INDEX idx_orders_branch_status  ON orders(branch_id, status);
CREATE INDEX idx_orders_branch_created ON orders(branch_id, created_at DESC);
CREATE INDEX idx_orders_customer       ON orders(customer_id);

CREATE TABLE order_items (
    id              BIGSERIAL PRIMARY KEY,
    order_id        BIGINT       NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id    INT          NOT NULL REFERENCES menu_items(id),
    promotion_id    INT          REFERENCES promotions(id),          -- KM đã áp dụng (nếu có)
    quantity        SMALLINT     NOT NULL CHECK (quantity BETWEEN 1 AND 20),
    original_price  INT          NOT NULL CHECK (original_price >= 0),  -- giá chi nhánh/giá chung trước KM
    unit_price      INT          NOT NULL CHECK (unit_price >= 0),      -- giá thực bán, chốt tại thời điểm đặt
    note            VARCHAR(255),                                     -- "ít đường, nhiều đá"
    status          item_status  NOT NULL DEFAULT 'WAITING',
    is_recommended  BOOLEAN      NOT NULL DEFAULT FALSE,              -- món thêm từ khối gợi ý (đo hiệu quả AI)
    started_at      TIMESTAMPTZ,
    done_at         TIMESTAMPTZ
);
CREATE INDEX idx_order_items_order ON order_items(order_id);
CREATE INDEX idx_order_items_menu  ON order_items(menu_item_id);
-- Hàng đợi màn hình Bar: món chưa xong, sắp theo giờ thanh toán của đơn
CREATE INDEX idx_order_items_queue ON order_items(status) WHERE status IN ('WAITING', 'PREPARING');

CREATE TABLE order_status_history (
    id           BIGSERIAL PRIMARY KEY,
    order_id     BIGINT        NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    from_status  order_status,
    to_status    order_status  NOT NULL,
    source       change_source NOT NULL,
    staff_id     INT           REFERENCES staff(id),
    created_at   TIMESTAMPTZ   NOT NULL DEFAULT now()
);
CREATE INDEX idx_osh_order ON order_status_history(order_id);

CREATE TABLE payments (
    id               BIGSERIAL PRIMARY KEY,
    order_id         BIGINT         NOT NULL UNIQUE REFERENCES orders(id),
    method           payment_method NOT NULL,
    amount           INT            NOT NULL CHECK (amount >= 0),
    status           payment_status NOT NULL,
    transaction_ref  VARCHAR(40)    NOT NULL UNIQUE,   -- mã giao dịch giả lập
    paid_at          TIMESTAMPTZ    NOT NULL DEFAULT now(),
    refunded_at      TIMESTAMPTZ
);

-- ---------- Tích điểm ----------
-- Điểm cộng khi đơn COMPLETED: floor(total_amount / 10000). Mỗi đơn cộng tối đa 1 lần.
CREATE TABLE loyalty_transactions (
    id           BIGSERIAL PRIMARY KEY,
    customer_id  INT          NOT NULL REFERENCES customers(id),
    order_id     BIGINT       UNIQUE REFERENCES orders(id),   -- NULL với giao dịch ADJUST
    points       INT          NOT NULL,
    type         loyalty_type NOT NULL,
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now()
);
CREATE INDEX idx_loyalty_customer ON loyalty_transactions(customer_id, created_at DESC);

-- ---------- AI gợi ý món ----------
CREATE TABLE recommendation_logs (
    id           BIGSERIAL PRIMARY KEY,
    branch_id    INT         NOT NULL REFERENCES branches(id),
    customer_id  INT         REFERENCES customers(id),
    order_id     BIGINT      REFERENCES orders(id),   -- gán sau khi khách đặt đơn
    mode         rec_mode    NOT NULL,                -- ẩn danh / thành viên
    context      JSONB       NOT NULL,                -- {temp_c, weather, hour, cart:[...]}
    items        JSONB       NOT NULL,                -- [{menu_item_id, score, reason}]
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ---------- Báo cáo ngày (dashboard) ----------
-- Job APScheduler chạy 00:05 hằng ngày, tổng hợp số liệu NGÀY HÔM TRƯỚC (giờ Asia/Ho_Chi_Minh)
-- cho từng chi nhánh rồi UPSERT vào bảng này. Dashboard chỉ đọc bảng này.
-- Doanh thu = tổng total_amount của các đơn đã thanh toán trong ngày (theo paid_at), không tính đơn đã hủy.
CREATE TABLE daily_sales_reports (
    branch_id               INT          NOT NULL REFERENCES branches(id),
    report_date             DATE         NOT NULL,
    order_count             INT          NOT NULL,              -- đơn đã thanh toán, không tính đơn hủy
    cancelled_count         INT          NOT NULL,
    revenue                 BIGINT       NOT NULL,              -- VND
    avg_order_value         INT          NOT NULL,              -- revenue / order_count
    avg_wait_seconds        INT,                                -- TB (ready_at - paid_at)
    member_order_ratio      NUMERIC(5,4) NOT NULL,              -- tỉ lệ đơn có customer_id
    promo_revenue           BIGINT       NOT NULL,              -- doanh thu từ món có promotion_id
    recommended_item_ratio  NUMERIC(5,4) NOT NULL,              -- tỉ lệ món có is_recommended
    top_items               JSONB        NOT NULL,              -- [{menu_item_id, name, qty}] top 5
    generated_at            TIMESTAMPTZ  NOT NULL DEFAULT now(),
    PRIMARY KEY (branch_id, report_date)
);

CREATE TABLE association_rules (
    id             SERIAL PRIMARY KEY,
    branch_id      INT          REFERENCES branches(id),     -- NULL = luật toàn chuỗi
    antecedent_id  INT          NOT NULL REFERENCES menu_items(id),
    consequent_id  INT          NOT NULL REFERENCES menu_items(id),
    support        NUMERIC(6,4) NOT NULL,
    confidence     NUMERIC(6,4) NOT NULL,
    lift           NUMERIC(8,4) NOT NULL,
    computed_at    TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CHECK (antecedent_id <> consequent_id)
);
CREATE INDEX idx_rules_lookup ON association_rules(branch_id, antecedent_id);
