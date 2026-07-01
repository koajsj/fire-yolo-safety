# -*- coding: utf-8 -*-
"""
SQLite 数据库访问层。
- 启动时自动建表
- 提供检测记录的增删查
- 提供系统设置（置信度阈值）的读写
"""
import sqlite3
from datetime import datetime
from typing import Optional

import config

RECORD_EXTRA_COLUMNS = {
    "risk_level": "TEXT DEFAULT '低风险'",
    "num_detections": "INTEGER DEFAULT 0",
    "fire_count": "INTEGER DEFAULT 0",
    "smoke_count": "INTEGER DEFAULT 0",
    "smoking_count": "INTEGER DEFAULT 0",
    "person_count": "INTEGER DEFAULT 0",
    "processing_time_ms": "INTEGER DEFAULT 0",
    "top_label": "TEXT DEFAULT '无'",
    "top_confidence": "REAL DEFAULT 0",
    "risk_message": "TEXT DEFAULT '当前未发现明显异常。'",
}

RECORD_DEFAULTS = {
    "risk_level": "低风险",
    "num_detections": 0,
    "fire_count": 0,
    "smoke_count": 0,
    "smoking_count": 0,
    "person_count": 0,
    "processing_time_ms": 0,
    "top_label": "无",
    "top_confidence": 0.0,
    "risk_message": "当前未发现明显异常。",
}


def get_conn() -> sqlite3.Connection:
    """获取数据库连接，开启行字典模式。"""
    conn = sqlite3.connect(str(config.DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """初始化数据库：建表 + 写入默认设置。"""
    conn = get_conn()
    cur = conn.cursor()

    # 检测记录表
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS records (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            detect_type  TEXT    NOT NULL,            -- image / video / camera
            classes      TEXT,                        -- 逗号分隔的中文类别
            confidence   REAL,                        -- 最高置信度
            is_abnormal  INTEGER DEFAULT 0,           -- 是否异常 0/1
            file_path    TEXT,                        -- 结果文件相对路径
            origin_path  TEXT,                        -- 原始文件相对路径
            detail       TEXT,                        -- JSON 字符串，详细检测结果
            created_at   TEXT    NOT NULL             -- 检测时间
        )
        """
    )

    _ensure_record_columns(cur)

    # 系统设置表（键值对）
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS settings (
            key   TEXT PRIMARY KEY,
            value TEXT
        )
        """
    )

    # 写入默认置信度阈值（仅当不存在时）
    cur.execute(
        "INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)",
        ("conf_threshold", str(config.DEFAULT_CONF_THRESHOLD)),
    )

    conn.commit()
    conn.close()


def _ensure_record_columns(cur) -> None:
    """兼容旧数据库：启动时自动补齐新增统计字段。"""
    existing = {
        row["name"]
        for row in cur.execute("PRAGMA table_info(records)").fetchall()
    }
    for name, column_sql in RECORD_EXTRA_COLUMNS.items():
        if name not in existing:
            cur.execute(f"ALTER TABLE records ADD COLUMN {name} {column_sql}")


def _normalize_record(row: dict) -> dict:
    """为旧记录和空字段补默认值，避免前端显示 undefined/null。"""
    data = dict(row)
    for key, value in RECORD_DEFAULTS.items():
        if data.get(key) is None:
            data[key] = value
    data["classes"] = data.get("classes") or ""
    data["confidence"] = float(data.get("confidence") or 0)
    data["top_confidence"] = float(data.get("top_confidence") or 0)
    data["is_abnormal"] = int(data.get("is_abnormal") or 0)
    for key in (
        "num_detections",
        "fire_count",
        "smoke_count",
        "smoking_count",
        "person_count",
        "processing_time_ms",
    ):
        data[key] = int(data.get(key) or 0)
    return data


# ---------------------------------------------------------------------------
# 设置相关
# ---------------------------------------------------------------------------
def get_conf_threshold() -> float:
    """读取当前置信度阈值。"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT value FROM settings WHERE key = 'conf_threshold'"
        ).fetchone()
    except sqlite3.OperationalError:
        conn.close()
        return config.DEFAULT_CONF_THRESHOLD
    conn.close()
    if row is None:
        return config.DEFAULT_CONF_THRESHOLD
    try:
        return float(row["value"])
    except (TypeError, ValueError):
        return config.DEFAULT_CONF_THRESHOLD


def set_conf_threshold(value: float) -> None:
    """更新置信度阈值。"""
    conn = get_conn()
    conn.execute(
        "INSERT INTO settings (key, value) VALUES ('conf_threshold', ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (str(value),),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# 记录相关
# ---------------------------------------------------------------------------
def add_record(
    detect_type: str,
    classes: str,
    confidence: float,
    is_abnormal: bool,
    file_path: str,
    origin_path: str,
    detail: str = "",
    risk_level: str = "低风险",
    num_detections: int = 0,
    fire_count: int = 0,
    smoke_count: int = 0,
    smoking_count: int = 0,
    person_count: int = 0,
    processing_time_ms: int = 0,
    top_label: str = "无",
    top_confidence: float = 0.0,
    risk_message: str = "当前未发现明显异常。",
) -> int:
    """新增一条检测记录，返回记录 id。"""
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO records
            (detect_type, classes, confidence, is_abnormal,
             file_path, origin_path, detail, created_at,
             risk_level, num_detections, fire_count, smoke_count, smoking_count,
             person_count, processing_time_ms, top_label, top_confidence, risk_message)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            detect_type,
            classes or "",
            round(float(confidence), 4),
            1 if is_abnormal else 0,
            file_path,
            origin_path,
            detail,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            risk_level or "低风险",
            int(num_detections or 0),
            int(fire_count or 0),
            int(smoke_count or 0),
            int(smoking_count or 0),
            int(person_count or 0),
            int(processing_time_ms or 0),
            top_label or "无",
            round(float(top_confidence or 0), 4),
            risk_message or "当前未发现明显异常。",
        ),
    )
    conn.commit()
    record_id = cur.lastrowid
    conn.close()
    return record_id


def list_records(
    keyword: Optional[str] = None,
    detect_type: Optional[str] = None,
    page: int = 1,
    page_size: int = 10,
):
    """分页查询检测记录，支持按类别关键字、检测类型过滤。"""
    page = max(1, int(page or 1))
    page_size = min(100, max(1, int(page_size or 10)))
    conn = get_conn()
    where = []
    params = []
    if keyword:
        where.append("classes LIKE ?")
        params.append(f"%{keyword}%")
    if detect_type:
        where.append("detect_type = ?")
        params.append(detect_type)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""

    total = conn.execute(
        f"SELECT COUNT(*) AS c FROM records {where_sql}", params
    ).fetchone()["c"]

    offset = (page - 1) * page_size
    rows = conn.execute(
        f"""
        SELECT * FROM records {where_sql}
        ORDER BY id DESC LIMIT ? OFFSET ?
        """,
        params + [page_size, offset],
    ).fetchall()
    conn.close()
    return total, [_normalize_record(dict(r)) for r in rows]


def get_record(record_id: int):
    """按 id 获取单条记录。"""
    conn = get_conn()
    row = conn.execute(
        "SELECT * FROM records WHERE id = ?", (record_id,)
    ).fetchone()
    conn.close()
    return _normalize_record(dict(row)) if row else None


def delete_record(record_id: int) -> bool:
    """删除一条记录。"""
    conn = get_conn()
    cur = conn.execute("DELETE FROM records WHERE id = ?", (record_id,))
    conn.commit()
    deleted = cur.rowcount > 0
    conn.close()
    return deleted


# ---------------------------------------------------------------------------
# 仪表盘统计
# ---------------------------------------------------------------------------
def dashboard_stats():
    """返回首页仪表盘所需的统计数据。"""
    conn = get_conn()
    today = datetime.now().strftime("%Y-%m-%d")

    total = conn.execute("SELECT COUNT(*) AS c FROM records").fetchone()["c"]
    today_total = conn.execute(
        "SELECT COUNT(*) AS c FROM records WHERE created_at LIKE ?",
        (f"{today}%",),
    ).fetchone()["c"]
    abnormal_total = conn.execute(
        "SELECT COUNT(*) AS c FROM records WHERE is_abnormal = 1"
    ).fetchone()["c"]
    high_risk_total = conn.execute(
        "SELECT COUNT(*) AS c FROM records WHERE risk_level = '高风险'"
    ).fetchone()["c"]
    medium_risk_total = conn.execute(
        "SELECT COUNT(*) AS c FROM records WHERE risk_level = '中风险'"
    ).fetchone()["c"]
    low_risk_total = conn.execute(
        """
        SELECT COUNT(*) AS c FROM records
        WHERE risk_level IS NULL OR risk_level = '' OR risk_level NOT IN ('高风险', '中风险')
        """
    ).fetchone()["c"]
    today_high_risk_total = conn.execute(
        "SELECT COUNT(*) AS c FROM records WHERE created_at LIKE ? AND risk_level = '高风险'",
        (f"{today}%",),
    ).fetchone()["c"]
    today_medium_risk_total = conn.execute(
        "SELECT COUNT(*) AS c FROM records WHERE created_at LIKE ? AND risk_level = '中风险'",
        (f"{today}%",),
    ).fetchone()["c"]
    today_low_risk_total = conn.execute(
        """
        SELECT COUNT(*) AS c FROM records
        WHERE created_at LIKE ? AND (risk_level IS NULL OR risk_level = '' OR risk_level NOT IN ('高风险', '中风险'))
        """,
        (f"{today}%",),
    ).fetchone()["c"]
    avg_processing_time_ms = conn.execute(
        "SELECT AVG(processing_time_ms) AS avg_ms FROM records WHERE processing_time_ms > 0"
    ).fetchone()["avg_ms"] or 0

    safety_score = max(0, min(100, 100 - today_high_risk_total * 18 - today_medium_risk_total * 8))

    # 类别分布（按逗号拆分后聚合，简单起见在 Python 端统计）
    class_rows = conn.execute(
        "SELECT classes FROM records WHERE classes IS NOT NULL AND classes != ''"
    ).fetchall()
    class_count = {}
    for r in class_rows:
        for c in str(r["classes"]).split(","):
            c = c.strip()
            if c:
                class_count[c] = class_count.get(c, 0) + 1

    # 检测方式占比
    type_rows = conn.execute(
        "SELECT detect_type, COUNT(*) AS c FROM records GROUP BY detect_type"
    ).fetchall()
    type_count = {r["detect_type"]: r["c"] for r in type_rows}

    risk_rows = conn.execute(
        """
        SELECT COALESCE(NULLIF(risk_level, ''), '低风险') AS risk_level, COUNT(*) AS c
        FROM records GROUP BY COALESCE(NULLIF(risk_level, ''), '低风险')
        """
    ).fetchall()
    risk_count = {"高风险": 0, "中风险": 0, "低风险": 0}
    for r in risk_rows:
        level = r["risk_level"] if r["risk_level"] in risk_count else "低风险"
        risk_count[level] += r["c"]

    # 最近 7 天每日趋势
    trend_rows = conn.execute(
        """
        SELECT substr(created_at, 1, 10) AS day, COUNT(*) AS c
        FROM records GROUP BY day ORDER BY day DESC LIMIT 7
        """
    ).fetchall()
    daily_trend = [{"day": r["day"], "count": r["c"]} for r in reversed(trend_rows)]

    # 最近 5 条记录
    recent = conn.execute(
        "SELECT * FROM records ORDER BY id DESC LIMIT 5"
    ).fetchall()

    conn.close()
    return {
        "total": total,
        "today_total": today_total,
        "abnormal_total": abnormal_total,
        "safety_score": round(safety_score, 1),
        "high_risk_total": high_risk_total,
        "medium_risk_total": medium_risk_total,
        "low_risk_total": low_risk_total,
        "today_high_risk_total": today_high_risk_total,
        "today_medium_risk_total": today_medium_risk_total,
        "today_low_risk_total": today_low_risk_total,
        "avg_processing_time_ms": int(round(avg_processing_time_ms)),
        "class_count": class_count,
        "type_count": type_count,
        "risk_count": risk_count,
        "daily_trend": daily_trend,
        "recent": [_normalize_record(dict(r)) for r in recent],
    }
