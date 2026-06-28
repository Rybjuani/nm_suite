from __future__ import annotations

import copy
import itertools
import re
from dataclasses import dataclass
from types import SimpleNamespace


@dataclass
class FakeResponse:
    data: object = None
    count: int | None = None
    error: object = None
    user: object = None
    session: object = None


class FakeSupabaseAuth:
    def __init__(self):
        self.signups: list[dict] = []
        self.signins: list[dict] = []
        self.recoveries: list[str] = []
        self._users_by_email: dict[str, dict] = {}

    def seed_user(self, email: str, password: str = "password123", user_id: str | None = None):
        user_id = user_id or f"user-{len(self._users_by_email) + 1}"
        self._users_by_email[email.lower()] = {"id": user_id, "email": email, "password": password}
        return self._users_by_email[email.lower()]

    def sign_up(self, credentials: dict):
        self.signups.append(copy.deepcopy(credentials))
        email = credentials.get("email", "").lower()
        if email in self._users_by_email:
            raise Exception("User already registered")
        user = self.seed_user(email, credentials.get("password", ""))
        session = {"access_token": "fake-access", "refresh_token": "fake-refresh"}
        return FakeResponse(
            data={"user": user, "session": session},
            user=SimpleNamespace(id=user["id"], email=user["email"]),
            session=SimpleNamespace(**session),
        )

    def sign_in_with_password(self, credentials: dict):
        self.signins.append(copy.deepcopy(credentials))
        email = credentials.get("email", "").lower()
        user = self._users_by_email.get(email)
        if not user or user.get("password") != credentials.get("password"):
            raise Exception("Invalid login credentials")
        session = {"access_token": "fake-access", "refresh_token": "fake-refresh"}
        return FakeResponse(
            data={"user": user, "session": session},
            user=SimpleNamespace(id=user["id"], email=user["email"]),
            session=SimpleNamespace(**session),
        )

    def reset_password_for_email(self, email: str):
        self.recoveries.append(email)
        return FakeResponse(data={"email": email})

    def set_session(self, access_token: str, refresh_token: str):
        return FakeResponse(data={"session": {"access_token": access_token, "refresh_token": refresh_token}})


class FakeSupabase:
    def __init__(self):
        self._rows: dict[str, list[dict]] = {}
        self._ids = itertools.count(1)
        self.auth = FakeSupabaseAuth()

    def table(self, table: str):
        self._rows.setdefault(table, [])
        return FakeTableQuery(self, table)

    def seed(self, table: str, rows):
        self._rows[table] = [copy.deepcopy(row) for row in rows]
        return self

    def all_rows(self, table: str):
        return [copy.deepcopy(row) for row in self._rows.get(table, [])]

    def _next_id(self) -> int:
        return next(self._ids)


class FakeTableQuery:
    def __init__(self, sb: FakeSupabase, table: str):
        self.sb = sb
        self.table_name = table
        self._op = "select"
        self._columns = "*"
        self._payload = None
        self._filters: list[tuple[str, str, object]] = []
        self._order: tuple[str, bool] | None = None
        self._limit: int | None = None
        self._range: tuple[int, int] | None = None
        self._single = False
        self._count: str | None = None
        self._on_conflict: tuple[str, ...] = ()

    def select(self, columns: str = "*", count: str | None = None):
        self._op = "select"
        self._columns = columns
        self._count = count
        return self

    def insert(self, payload):
        self._op = "insert"
        self._payload = payload
        return self

    def update(self, payload: dict):
        self._op = "update"
        self._payload = payload
        return self

    def delete(self):
        self._op = "delete"
        return self

    def upsert(self, payload, on_conflict: str | None = None, **_kwargs):
        self._op = "upsert"
        self._payload = payload
        self._on_conflict = tuple(
            part.strip() for part in (on_conflict or "id").split(",") if part.strip()
        )
        return self

    def eq(self, column: str, value):
        self._filters.append(("eq", column, value))
        return self

    def neq(self, column: str, value):
        self._filters.append(("neq", column, value))
        return self

    def like(self, column: str, pattern: str):
        self._filters.append(("like", column, pattern))
        return self

    def ilike(self, column: str, pattern: str):
        self._filters.append(("ilike", column, pattern))
        return self

    def in_(self, column: str, values):
        self._filters.append(("in", column, list(values)))
        return self

    def gte(self, column: str, value):
        self._filters.append(("gte", column, value))
        return self

    def gt(self, column: str, value):
        self._filters.append(("gt", column, value))
        return self

    def lte(self, column: str, value):
        self._filters.append(("lte", column, value))
        return self

    def lt(self, column: str, value):
        self._filters.append(("lt", column, value))
        return self

    def order(self, column: str, desc: bool = False, **_kwargs):
        self._order = (column, bool(desc))
        return self

    def limit(self, count: int):
        self._limit = count
        return self

    def range(self, start: int, end: int):
        self._range = (start, end)
        return self

    def single(self):
        self._single = True
        return self

    def execute(self):
        if self._op == "insert":
            data = self._insert_rows(self._payload)
        elif self._op == "update":
            data = self._update_rows(self._payload)
        elif self._op == "delete":
            data = self._delete_rows()
        elif self._op == "upsert":
            data = self._upsert_rows(self._payload)
        else:
            data = self._selected_rows()
        if self._single:
            data = data[0] if data else None
        return FakeResponse(data=data, count=len(data) if isinstance(data, list) and self._count else None)

    def _selected_rows(self) -> list[dict]:
        rows = [copy.deepcopy(row) for row in self.sb._rows.get(self.table_name, [])]
        rows = [row for row in rows if self._matches(row)]
        if self._order:
            column, desc = self._order
            rows.sort(key=lambda row: row.get(column), reverse=desc)
        if self._range:
            start, end = self._range
            rows = rows[start : end + 1]
        if self._limit is not None:
            rows = rows[: self._limit]
        return [self._project(row) for row in rows]

    def _insert_rows(self, payload):
        rows = payload if isinstance(payload, list) else [payload]
        inserted = []
        for row in rows:
            new_row = copy.deepcopy(row)
            if "id" not in new_row:
                new_row["id"] = self.sb._next_id()
            self.sb._rows.setdefault(self.table_name, []).append(new_row)
            inserted.append(copy.deepcopy(new_row))
        return inserted

    def _update_rows(self, payload: dict):
        updated = []
        for row in self.sb._rows.get(self.table_name, []):
            if self._matches(row):
                row.update(copy.deepcopy(payload))
                updated.append(copy.deepcopy(row))
        return updated

    def _delete_rows(self):
        kept = []
        deleted = []
        for row in self.sb._rows.get(self.table_name, []):
            if self._matches(row):
                deleted.append(copy.deepcopy(row))
            else:
                kept.append(row)
        self.sb._rows[self.table_name] = kept
        return deleted

    def _upsert_rows(self, payload):
        rows = payload if isinstance(payload, list) else [payload]
        result = []
        table_rows = self.sb._rows.setdefault(self.table_name, [])
        for row in rows:
            new_row = copy.deepcopy(row)
            conflict = self._on_conflict or (("id",) if "id" in new_row else tuple())
            match = None
            if conflict:
                for existing in table_rows:
                    if all(existing.get(key) == new_row.get(key) for key in conflict):
                        match = existing
                        break
            if match is None:
                if "id" not in new_row:
                    new_row["id"] = self.sb._next_id()
                table_rows.append(new_row)
                result.append(copy.deepcopy(new_row))
            else:
                match.update(new_row)
                result.append(copy.deepcopy(match))
        return result

    def _matches(self, row: dict) -> bool:
        for op, column, value in self._filters:
            actual = row.get(column)
            if op == "eq" and actual != value:
                return False
            if op == "neq" and actual == value:
                return False
            if op == "in" and actual not in value:
                return False
            if op == "gte" and not (actual >= value):
                return False
            if op == "gt" and not (actual > value):
                return False
            if op == "lte" and not (actual <= value):
                return False
            if op == "lt" and not (actual < value):
                return False
            if op in {"like", "ilike"}:
                actual_s = "" if actual is None else str(actual)
                pattern = re.escape(str(value)).replace("%", ".*")
                flags = re.IGNORECASE if op == "ilike" else 0
                if re.fullmatch(pattern, actual_s, flags=flags) is None:
                    return False
        return True

    def _project(self, row: dict) -> dict:
        if not self._columns or self._columns == "*":
            return row
        fields = []
        for part in self._columns.split(","):
            field = part.strip()
            if not field or "(" in field:
                continue
            fields.append(field)
        if not fields:
            return row
        return {field: row.get(field) for field in fields if field in row}
