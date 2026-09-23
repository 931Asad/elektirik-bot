import re
import sqlite3
from contextlib import closing

from config import DB_PATH


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    with closing(get_conn()) as conn, conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS objects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                obj_type TEXT NOT NULL,           -- 'TP' yoki 'GTP'
                number TEXT NOT NULL,             -- foydalanuvchi kiritgan nom, masalan "123"
                norm_number TEXT NOT NULL,        -- qidiruv uchun normallashtirilgan (faqat raqam+harf)
                address TEXT,
                lat REAL,
                lon REAL,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                object_id INTEGER NOT NULL REFERENCES objects(id) ON DELETE CASCADE,
                file_id TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                norm_name TEXT NOT NULL,
                start_lat REAL NOT NULL,
                start_lon REAL NOT NULL,
                end_lat REAL NOT NULL,
                end_lon REAL NOT NULL,
                description TEXT,
                created_by INTEGER,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS allowed_users (
                user_id INTEGER PRIMARY KEY,
                full_name TEXT,
                added_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _clean(text: str) -> str:
    """Katta harfga o'tkazadi va harf/raqamdan boshqa hammasini olib tashlaydi."""
    text = text.upper().replace("Ё", "Е")
    return re.sub(r"[^A-ZА-Я0-9]", "", text)


_OBJ_PREFIXES = ("GTP", "ГТП", "TP", "ТП")  # uzunroqlari oldin tekshiriladi


def normalize(text: str) -> str:
    """ТП/ГТП qidiruvi uchun: 'ТП-123', 'tp123', ' 123 ' -> '123'.
    Boshidagi ТП/ГТП/TP/GTP prefiksi olib tashlanadi, shunda foydalanuvchi
    faqat raqam yozsa ham, prefiks bilan yozsa ham bir xil natija chiqadi."""
    cleaned = _clean(text)
    for prefix in _OBJ_PREFIXES:
        if cleaned.startswith(prefix) and len(cleaned) > len(prefix):
            return cleaned[len(prefix):]
    return cleaned


def normalize_line(text: str) -> str:
    """Liniya nomi uchun: 'Л-12', 'l12', 'Л 12' -> '12'.
    Boshidagi bitta Л yoki L harfi (lotin/kirill farqisiz) olib tashlanadi."""
    cleaned = _clean(text)
    if cleaned[:1] in ("Л", "L") and len(cleaned) > 1:
        return cleaned[1:]
    return cleaned


# ---------- OBJECTS (TP / GTP) ----------

def add_object(obj_type: str, number: str, address: str, lat: float, lon: float, created_by: int) -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO objects (obj_type, number, norm_number, address, lat, lon, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (obj_type, number, normalize(number), address, lat, lon, created_by),
        )
        return cur.lastrowid


def add_photo(object_id: int, file_id: str):
    with closing(get_conn()) as conn, conn:
        conn.execute("INSERT INTO photos (object_id, file_id) VALUES (?, ?)", (object_id, file_id))


def find_objects(query: str):
    norm = normalize(query)
    if not norm:
        return []
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM objects WHERE norm_number = ? OR norm_number LIKE ? ORDER BY id DESC",
            (norm, f"%{norm}%"),
        ).fetchall()
    return rows


def get_object(object_id: int):
    with closing(get_conn()) as conn:
        return conn.execute("SELECT * FROM objects WHERE id = ?", (object_id,)).fetchone()


def get_photos(object_id: int):
    with closing(get_conn()) as conn:
        return conn.execute("SELECT file_id FROM photos WHERE object_id = ?", (object_id,)).fetchall()


def delete_object(object_id: int):
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM objects WHERE id = ?", (object_id,))


# ---------- LINES ----------

def add_line(name: str, start_lat: float, start_lon: float, end_lat: float, end_lon: float,
             description: str, created_by: int) -> int:
    with closing(get_conn()) as conn, conn:
        cur = conn.execute(
            "INSERT INTO lines (name, norm_name, start_lat, start_lon, end_lat, end_lon, description, created_by) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (name, normalize_line(name), start_lat, start_lon, end_lat, end_lon, description, created_by),
        )
        return cur.lastrowid


def find_lines(query: str):
    norm = normalize_line(query)
    if not norm:
        return []
    with closing(get_conn()) as conn:
        rows = conn.execute(
            "SELECT * FROM lines WHERE norm_name = ? OR norm_name LIKE ? ORDER BY id DESC",
            (norm, f"%{norm}%"),
        ).fetchall()
    return rows


def get_line(line_id: int):
    with closing(get_conn()) as conn:
        return conn.execute("SELECT * FROM lines WHERE id = ?", (line_id,)).fetchone()


def delete_line(line_id: int):
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM lines WHERE id = ?", (line_id,))


# ---------- ACCESS CONTROL ----------

def is_allowed(user_id: int, admin_ids: set) -> bool:
    if user_id in admin_ids:
        return True
    with closing(get_conn()) as conn:
        row = conn.execute("SELECT 1 FROM allowed_users WHERE user_id = ?", (user_id,)).fetchone()
    return row is not None


def add_allowed_user(user_id: int, full_name: str):
    with closing(get_conn()) as conn, conn:
        conn.execute(
            "INSERT OR REPLACE INTO allowed_users (user_id, full_name) VALUES (?, ?)",
            (user_id, full_name),
        )


def remove_allowed_user(user_id: int):
    with closing(get_conn()) as conn, conn:
        conn.execute("DELETE FROM allowed_users WHERE user_id = ?", (user_id,))


def list_allowed_users():
    with closing(get_conn()) as conn:
        return conn.execute("SELECT * FROM allowed_users ORDER BY added_at").fetchall()


def stats():
    with closing(get_conn()) as conn:
        objs = conn.execute("SELECT COUNT(*) c FROM objects").fetchone()["c"]
        lns = conn.execute("SELECT COUNT(*) c FROM lines").fetchone()["c"]
        users = conn.execute("SELECT COUNT(*) c FROM allowed_users").fetchone()["c"]
    return objs, lns, users
