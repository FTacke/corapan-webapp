"""Counter services for access, visits, and search telemetry."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import json
from datetime import datetime

DATA_ROOT = Path(__file__).resolve().parents[3] / "data"
COUNTER_ROOT = DATA_ROOT / "counters"
COUNTER_ROOT.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class CounterStore:
    filename: str
    default: dict[str, Any]
    _cache: dict[str, Any] = field(default_factory=dict, init=False)

    def path(self) -> Path:
        return COUNTER_ROOT / self.filename

    def load(self) -> dict[str, Any]:
        if self._cache:
            return self._cache
        if not self.path().exists():
            self._cache = json.loads(json.dumps(self.default))
            self.persist()
            return self._cache
        with self.path().open("r", encoding="utf-8") as handle:
            self._cache = json.load(handle)
        return self._cache

    def persist(self) -> None:
        self.path().parent.mkdir(parents=True, exist_ok=True)
        with self.path().open("w", encoding="utf-8") as handle:
            json.dump(self._cache or self.default, handle, indent=2)


class AccessCounter(CounterStore):
    def increment(self, account: str, role: str) -> None:
        payload = self.load()
        now = datetime.utcnow()
        month_key = now.strftime("%Y-%m")
        day_value = now.strftime("%Y-%m-%d")

        total = payload.setdefault("total", {"overall": 0, "monthly": {}, "days": []})
        total["overall"] += 1
        total.setdefault("monthly", {})[month_key] = total["monthly"].get(month_key, 0) + 1
        total.setdefault("days", []).append(day_value)

        roles = payload.setdefault("roles", {})
        role_bucket = roles.setdefault(role, {"overall": 0, "monthly": {}, "days": []})
        role_bucket["overall"] += 1
        role_bucket.setdefault("monthly", {})[month_key] = role_bucket["monthly"].get(month_key, 0) + 1
        role_bucket.setdefault("days", []).append(day_value)

        accounts = payload.setdefault("accounts", {})
        account_bucket = accounts.setdefault(account, {"overall": 0, "monthly": {}, "days": []})
        account_bucket["overall"] += 1
        account_bucket.setdefault("monthly", {})[month_key] = account_bucket["monthly"].get(month_key, 0) + 1
        account_bucket.setdefault("days", []).append(day_value)
        self.persist()


class SimpleCounter(CounterStore):
    def increment(self, amount: int = 1) -> None:
        payload = self.load()
        payload["overall"] = payload.get("overall", 0) + amount
        self.persist()


counter_access = AccessCounter(
    filename="counter_access.json",
    default={"total": {"overall": 0, "monthly": {}, "days": []}, "roles": {}, "accounts": {}},
)

counter_visits = SimpleCounter(
    filename="counter_visits.json",
    default={"overall": 0},
)

counter_search = SimpleCounter(
    filename="counter_search.json",
    default={"overall": 0},
)