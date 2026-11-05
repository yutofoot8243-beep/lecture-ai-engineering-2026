# 第3回 解答

## 演習

- 第1回（素のLLM）とエージェントの回答の違い：
  - 第1回の app.ask は、AIE2026 を知らないまま「一般的には」と前置きし、Level 1〜3（基礎・初級／応用・中級／発展・上級）ともっともらしく推測で答えた。「どれか1つで完了」「原則採点しない」には触れなかった
  - 第3回の app.agent は、先に search_glossary('3レベル') で用語集を引き、「基礎（講義内容の確認）・実装（自分でコードを書く）・発展（調査や試行）のどれか1つで完了、原則採点しない」と、data/glossary.json の定義どおりに答えた。最後に（第1回）と関係する回も示した
- `--trace` で見えたツール呼び出し（ツール名と引数）：
  - 「3レベル」：`search_glossary({'query': '3レベル'})`
  - 「LoRAとQLoRAの違いは？」：`search_glossary({'query': 'LoRA'})` と `search_glossary({'query': 'QLoRA'})`。docstring の「query には調べたい用語を1つだけ入れる」のとおり、用語を分けて検索した。2つは1回の応答でまとめて（並列に）呼ばれた
  - 「第2回の内容から確認問題を1問出して」：`make_quiz({'lecture': 2})`
- 1つの質問での LLM 呼び出し回数（`requests`）：
  - 3問とも requests=2（1回目でツール呼び出しを出力 → ツールの結果を受けて2回目で回答）。LoRA/QLoRA は tool_calls=2 だが、同じ応答でまとめて呼んだので requests は 2 のまま
  - 入力 / 出力トークン：3レベル 933 / 189、LoRA・QLoRA 1346 / 225、確認問題 910 / 113
- 追加したツールと、docstring に書いた説明：
  - `make_quiz(lecture: int) -> str`：用語集から指定した回の用語を1つ選び、`{"question": "「○○」の意味は？", "answer": 定義}` を JSON 文字列で返す。該当する用語が無い回（lecture=0 など）は「第N回の用語は用語集にありません。」を返す
  - docstring：「指定した回の用語から1つを選び、確認問題と答えを返す。『第2回の確認問題を出して』のように、復習用の問題を求められたときに使う。」
  - 「第2回の内容から確認問題を1問出して」で make_quiz({'lecture': 2}) が呼ばれ、LoRA の問題が出た。答えはそのまま書かず「答えのヒント」として示した（INSTRUCTIONS の「答えそのものは書かず、ヒントで導く」が効いたと考えられる）
  - `uv run pytest -q`：17 passed

## 宿題

- 取り組んだレベル：発展（a）ADK で作り直す
- やったこと：
  - `adk_agent/glossary_agent/agent.py` と `__init__.py`（`from . import agent`）を作成した。`INSTRUCTIONS`、3つのツール（search_glossary・get_lecture_summary・make_quiz）、モデル名（`app.config.MODEL` = gemini-3.5-flash-lite）は `app/` から import してそのまま使い、`app/` は変更していない
  - `PYTHONPATH=. uv run --with google-adk adk run --in_memory --jsonl adk_agent/glossary_agent "<質問>"` で実行した（google-adk 2.13.0。講座で固定の google-genai 2.31.0 と共存できた）。`--in_memory` で毎回新しいセッションにし、`--jsonl` でイベント（functionCall / functionResponse）を表示して `--trace` の代わりにした
  - 演習と同じ 3 つの質問を、Pydantic AI 版（`app.agent --trace`）と ADK 版で比べた
- 結果：
  - 書き方の違い

    | 観点 | Pydantic AI（app/agent.py） | ADK（adk_agent/glossary_agent/agent.py） |
    |---|---|---|
    | 指示 | `Agent(instructions=INSTRUCTIONS)` | `Agent(instruction=INSTRUCTIONS)` |
    | ツール登録 | 作った後で `agent.tool_plain(fn)` を1つずつ | 作るときに `tools=[fn, ...]` で渡す |
    | モデル | 実行時に `run_sync(..., model=...)`（テストで TestModel に差し替えるため） | 作るときに `model="..."` で固定 |
    | 名前 | 不要 | `name` が必須。指示にも使われる |
    | 実行 | 自作の CLI（`python -m app.agent`） | `adk run`（`root_agent` という変数名を探して読み込む） |
    | ツール呼び出しの確認 | 自作の `--trace`（[tool call] / [tool return] / requests） | `--jsonl` のイベント。呼び出しIDで依頼と結果が対応する。requests のまとめは無く、イベントを数える |

  - 回答の違い（モデルはどちらも gemini-3.5-flash-lite、各1回）

    | 質問 | ツール呼び出し（両者同じ） | 入力トークン PAI → ADK | 出力トークン PAI → ADK | 回答 |
    |---|---|---|---|---|
    | 宿題の3レベル | search_glossary('3レベル') | 933 → 1059（+126） | 189 → 122 | 内容は同じ。最後に第1回 |
    | LoRAとQLoRAの違い | search_glossary('LoRA')・('QLoRA') を1回の応答でまとめて | 1346 → 1470（+124） | 225 → 200 | ほぼ同じ構成。最後に第2回 |
    | 第2回の確認問題 | make_quiz({'lecture': 2}) | 910 → 1036（+126） | 113 → 61 | PAI は問題＋答えのヒント、ADK は問題だけで答え・ヒントなし |

    どちらも LLM 呼び出しは 2 回（ツール呼び出し → 回答）。PAI = Pydantic AI。
  - ADK が実際にモデルへ送る指示を `before_model_callback` で取り出すと、INSTRUCTIONS の後ろに `You are an agent. Your internal name is "glossary_agent".` の1行が自動で足されていた。ツールの説明は docstring がそのまま渡っていた
- 気づき・疑問：
  - 同じモデル・同じ指示・同じ docstring なら、ハーネスを替えても「どのツールを、どの引数で、何回呼ぶか」は 3 問とも一致した。ツールの使い方は、フレームワークよりも指示文と docstring で決まっている
  - 一方、入力トークンは ADK の方が毎回ほぼ一定（+124〜126）多かった。ハーネスが見えないところで指示を足している（名前の1行は確認できた）。残りの差はツール定義の形式の違いと考えているが、未確認。講義の「同じモデルでもハーネスで費用が変わる」を小さく確かめられた
  - 確認問題の出し方（ヒントを出すか）は違ったが、各 1 回の実行なので、ハーネスの差か出力のゆらぎかは区別できていない。複数回実行して比べる必要がある
  - ADK 版の LoRA/QLoRA で 503 が 2 回続いた。jsonl を見ると、ツールの実行は終わったあと、回答を作る 2 回目のモデル呼び出しで失敗しており、ADK は自動では再試行せず終了した。やり直すとツールも最初から呼び直される。search_glossary は読み取りだけなので問題ないが、送信や保存のような取り消せないツールなら二重実行になりうる（冪等性・失敗時の振る舞い）
  - 書き方は ADK の方が短いが、モデルを作るときに固定するため、Pydantic AI の `agent.override(model=TestModel())` のように API キーなしでテストする方法は ADK ではどう書くのかが疑問として残った
