"""Shared helpers used across all generators."""

import random
import numpy as np
from datetime import date, timedelta, datetime
from dateutil.relativedelta import relativedelta
from faker import Faker

fake = Faker("en_PK")
Faker.seed(42)

# ── Date helpers ─────────────────────────────────────────────────────

def random_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=random.randint(0, delta))

def random_datetime(start: date, end: date) -> datetime:
    d = random_date(start, end)
    h = random.randint(6, 22)
    m = random.randint(0, 59)
    s = random.randint(0, 59)
    return datetime(d.year, d.month, d.day, h, m, s)

def date_range_dates(start: date, end: date):
    """Yield every date between start and end inclusive."""
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)

# ── Pakistani name helpers ────────────────────────────────────────────

MALE_FIRST = [
    "Muhammad", "Ahmed", "Ali", "Hassan", "Usman", "Omar", "Bilal",
    "Imran", "Tariq", "Asad", "Kashif", "Shoaib", "Zubair", "Hamza",
    "Faisal", "Saad", "Waqar", "Nasir", "Adeel", "Sohail", "Zain",
    "Raza", "Kamran", "Junaid", "Arif", "Salman", "Rizwan", "Fahad",
]
FEMALE_FIRST = [
    "Fatima", "Ayesha", "Sara", "Hina", "Sana", "Nadia", "Amna",
    "Rabia", "Zara", "Maryam", "Aisha", "Noor", "Saima", "Mehwish",
    "Uzma", "Robia", "Asma", "Bushra", "Sumera", "Laiba",
]
LAST_NAMES = [
    "Khan", "Ali", "Ahmed", "Sheikh", "Malik", "Butt", "Chaudhry",
    "Iqbal", "Hussain", "Raza", "Mirza", "Siddiqui", "Qureshi",
    "Ansari", "Bhatti", "Hashmi", "Nawaz", "Rizvi", "Bajwa",
    "Gondal", "Rana", "Raja", "Javed", "Mehmood", "Farooq",
]

def pak_male_name() -> str:
    return f"{random.choice(MALE_FIRST)} {random.choice(LAST_NAMES)}"

def pak_female_name() -> str:
    return f"{random.choice(FEMALE_FIRST)} {random.choice(LAST_NAMES)}"

def pak_name(gender: str = None) -> str:
    if gender is None:
        gender = random.choice(["M", "F"])
    return pak_male_name() if gender == "M" else pak_female_name()

def pak_phone() -> str:
    prefix = random.choice(["0300", "0301", "0311", "0312", "0320", "0321",
                             "0333", "0345", "0346", "0315"])
    return f"{prefix}-{random.randint(1000000, 9999999)}"

def pak_cnic() -> str:
    """Format: DDDDD-DDDDDDD-D"""
    return f"{random.randint(10000,99999)}-{random.randint(1000000,9999999)}-{random.randint(1,9)}"

def pak_license_no() -> str:
    provinces = ["ISB", "PB", "KPK", "SND", "BLN"]
    p = random.choice(provinces)
    return f"{p}-{random.randint(100000,999999)}"

# ── ID generators ─────────────────────────────────────────────────────

def make_id(prefix: str, n: int, zero_pad: int = 5) -> str:
    return f"{prefix}{str(n).zfill(zero_pad)}"

# ── Weighted random choice ────────────────────────────────────────────

def weighted_choice(items, weights):
    total = sum(weights)
    r = random.uniform(0, total)
    upto = 0
    for item, w in zip(items, weights):
        upto += w
        if r <= upto:
            return item
    return items[-1]

# ── Numeric jitter ───────────────────────────────────────────────────

def jitter(value: float, pct: float = 0.10) -> float:
    """Apply ±pct% random noise to a value."""
    return value * (1 + random.uniform(-pct, pct))
