from pathlib import Path

from .services import ReportService, create_admin_report


def run() -> None:
    service = ReportService(Path("."))
    report = service.build_report("Ada Lovelace", "ADA@example.com")
    service.save_report(report)
    create_admin_report("Grace Hopper", "GRACE@example.com")


if __name__ == "__main__":
    run()
