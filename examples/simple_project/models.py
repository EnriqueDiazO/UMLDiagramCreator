from dataclasses import dataclass


@dataclass
class User:
    """Person that owns reports."""

    name: str
    email: str

    def display_name(self) -> str:
        return self.name.title()


class AdminUser(User):
    """User with elevated permissions."""

    def can_manage(self) -> bool:
        return True


class Report:
    def __init__(self, owner: User, title: str) -> None:
        self.owner = owner
        self.title = title
        self.rows = []

    @property
    def row_count(self) -> int:
        return len(self.rows)

    def add_row(self, value: str) -> None:
        self.rows.append(value)

    def summary(self) -> str:
        return format_report_title(self.title)


def format_report_title(title: str) -> str:
    return title.strip().title()
