"""第1回 宿題（発展）scripts/bench_ask.py の集計のテスト（LLMもAPIキーも使わない）。"""

from scripts.bench_ask import Record, interval_for, summarize


def test_summarize_averages_success_and_lists_errors():
    records = [
        Record("m", "short", 1.0, input_tokens=10, output_tokens=4, thoughts_tokens=0),
        Record("m", "short", 3.0, input_tokens=10, output_tokens=6, thoughts_tokens=10),
        Record("m", "short", 0.2, error=429),
    ]
    row = summarize(records).splitlines()[2]
    # 成功2回の平均：応答時間2.0秒、出力5、思考5。速度は (4/1 + 16/3) / 2
    assert row == "| m | short | 2/3 | 2.0 | 10.0 | 5.0 | 5.0 | 4.7 | 429 |"


def test_summarize_all_errors():
    row = summarize([Record("m", "course", 0.1, error=503)]).splitlines()[2]
    assert row == "| m | course | 0/1 | - | - | - | - | - | 503 |"


def test_interval_respects_rate_limit():
    assert interval_for("gemini-3.8-flash") > 60 / 5
    assert interval_for("unknown-model") == interval_for("gemini-3.8-flash")


def test_summarize_lists_timeout_with_api_errors():
    records = [Record("m", "short", 120.0, error="timeout"), Record("m", "short", 0.2, error=429)]
    row = summarize(records).splitlines()[2]
    assert row.endswith("| 429, timeout |")
