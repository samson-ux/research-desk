"""`python -m research_desk` prints the command map. It does not run live research."""

from __future__ import annotations


def main() -> int:
    print(
        "\n".join(
            [
                "research_desk commands",
                "  python -m research_desk.check_latest",
                "  python -m research_desk.show_rubric",
                "  python -m research_desk.run --fixture",
                "  python -m research_desk.run --integrity-samples",
                "  python -m research_desk.run --live",
                "  python -m research_desk.paper_journal log|mark|report",
                "  python -m research_desk.daily_report",
                "Live research is blocked until the rubric in show_rubric is approved.",
            ]
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
