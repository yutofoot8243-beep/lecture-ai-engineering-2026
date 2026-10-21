"""第1回 宿題（発展）: 応答時間とトークン数を、モデル・質問ごとに計測して比べる。

使い方:
    uv run python -m scripts.bench_ask
    uv run python -m scripts.bench_ask --models gemini-3.5-flash-lite --repeats 3
    # レート制限を観察する（待ち時間なしで連続して送る。1日の上限を消費するので注意）
    uv run python -m scripts.bench_ask --models gemini-3.5-flash-lite --questions short --repeats 20 --interval 0

1回ごとの結果を表示し、最後にモデル×質問ごとの平均を Markdown の表で出す（answer.md に貼れる）。
無料枠の上限（毎分のリクエスト数）を超えないよう、既定ではモデルごとに間隔をあけて送る。
"""

import argparse
import statistics
import time
from dataclasses import dataclass

from google import genai
from google.genai import errors

from app.ask import DEFAULT_QUESTION
from app.config import api_error_message, get_api_key

QUESTIONS = {
    "short": "日本の首都はどこですか？一言で答えてください。",
    "general": "LoRAとは何ですか？",
    "course": DEFAULT_QUESTION,
}
DEFAULT_MODELS = ["gemini-3.5-flash-lite", "gemini-3.8-flash"]

# 無料枠の毎分リクエスト数（講座の実測）。知らないモデルは控えめに 5 とみなす
RPM = {"gemini-3.5-flash-lite": 15, "gemini-3.8-flash": 5}


@dataclass
class Record:
    model: str
    question: str
    seconds: float
    error: int | None = None  # APIエラーのステータスコード（成功なら None）
    input_tokens: int | None = None
    output_tokens: int | None = None
    thoughts_tokens: int | None = None  # 思考（thinking）に使ったトークン。出力とは別に数えられる
    output_chars: int = 0


def interval_for(model: str) -> float:
    """毎分の上限を超えないための、リクエストの間隔（秒）。1割の余裕を持たせる。"""
    return 60 / RPM.get(model, 5) * 1.1


def measure(client: genai.Client, model: str, key: str) -> Record:
    start = time.perf_counter()
    try:
        response = client.models.generate_content(model=model, contents=QUESTIONS[key])
    except errors.APIError as e:
        print(f"  ! {api_error_message(e.code, e.message)}")
        return Record(model, key, time.perf_counter() - start, error=e.code)
    seconds = time.perf_counter() - start

    usage = response.usage_metadata
    return Record(
        model,
        key,
        seconds,
        input_tokens=usage.prompt_token_count if usage else None,
        output_tokens=usage.candidates_token_count if usage else None,
        thoughts_tokens=(usage.thoughts_token_count or 0) if usage else None,
        output_chars=len(response.text or ""),
    )


def mean(values: list) -> str:
    values = [v for v in values if v is not None]
    return f"{statistics.mean(values):.1f}" if values else "-"


def summarize(records: list[Record]) -> str:
    """モデル×質問ごとの平均を Markdown の表にする。出力速度は（出力＋思考）トークン ÷ 秒。"""
    lines = [
        "| モデル | 質問 | 成功/回数 | 応答時間(秒) | 入力 | 出力 | 思考 | 出力速度(tok/s) | エラー |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    groups: dict[tuple[str, str], list[Record]] = {}
    for r in records:
        groups.setdefault((r.model, r.question), []).append(r)

    for (model, key), rs in groups.items():
        ok = [r for r in rs if r.error is None]
        speeds = [
            ((r.output_tokens or 0) + (r.thoughts_tokens or 0)) / r.seconds
            for r in ok
            if r.seconds > 0
        ]
        errs = sorted({r.error for r in rs if r.error is not None})
        lines.append(
            f"| {model} | {key} | {len(ok)}/{len(rs)} | {mean([r.seconds for r in ok])} "
            f"| {mean([r.input_tokens for r in ok])} | {mean([r.output_tokens for r in ok])} "
            f"| {mean([r.thoughts_tokens for r in ok])} | {mean(speeds)} "
            f"| {', '.join(map(str, errs)) or '-'} |"
        )
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="応答時間とトークン数を計測する")
    parser.add_argument("--models", nargs="+", default=DEFAULT_MODELS)
    parser.add_argument("--questions", nargs="+", choices=QUESTIONS, default=list(QUESTIONS))
    parser.add_argument("--repeats", type=int, default=2, help="同じ質問を何回ずつ送るか")
    parser.add_argument("--interval", type=float, default=None, help="リクエストの間隔（秒）。省略時はモデルの上限から決める")
    args = parser.parse_args()

    client = genai.Client(api_key=get_api_key())
    records = []
    for model in args.models:
        wait = interval_for(model) if args.interval is None else args.interval
        print(f"[model] {model}（間隔 {wait:.1f} 秒）")
        for key in args.questions:
            for i in range(args.repeats):
                if records:
                    time.sleep(wait)
                r = measure(client, model, key)
                records.append(r)
                status = f"error={r.error}" if r.error else (
                    f"input={r.input_tokens} output={r.output_tokens} thoughts={r.thoughts_tokens} chars={r.output_chars}"
                )
                print(f"  {key} #{i + 1}: {r.seconds:.2f}s {status}")

    print("\n" + summarize(records))


if __name__ == "__main__":
    main()
