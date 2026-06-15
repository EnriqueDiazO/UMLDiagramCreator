from pathlib import Path

from .models import AdminUser, Report, User, format_report_title
from .utils import normalize_email, save_payload


class ReportService:
    def __init__(self, output_dir: Path) -> None:
        self.output_dir = output_dir

    @classmethod
    def for_current_dir(cls) -> "ReportService":
        return cls(Path.cwd())

    @staticmethod
    def default_title() -> str:
        return "weekly report"

    def build_report(self, name: str, email: str) -> Report:
        user = User(name=name, email=normalize_email(email))
        report = Report(user, format_report_title(self.default_title()))
        report.add_row(user.display_name())
        return report

    def save_report(self, report: Report) -> None:
        payload = {"title": report.title, "rows": report.row_count}
        save_payload(self.output_dir / "report.json", payload)


def create_admin_report(name: str, email: str) -> Report:
    admin = AdminUser(name=name, email=normalize_email(email))
    report = Report(admin, "Admin Report")
    report.add_row(admin.display_name())
    return report
