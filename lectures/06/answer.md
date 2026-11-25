# 第6回 解答

## 演習

<!-- [tool call] の行は、表示された行をそのまま貼り付けてください。終わらなかった STEP は、空欄のままでかまいません。 -->

- STEP 1 のツールの名前：glossary_search_glossary
- STEP 2 の [tool call]：`[tool call]   glossary_search_glossary({'query': '3レベル'})`
- STEP 3 の [tool call]：`[tool call]   fetch_fetch({'url': 'https://modelcontextprotocol.io/'})`
  - このあと `glossary_search_glossary({'query': 'MCP'})` も呼ばれた（モデル応答 3 回）
- STEP 4 の [tool call]：`[tool call]   aws_aws___search_documentation({'topics': ['general'], 'search_phrase': 'Amazon S3 Versioning overview'})`
- 気づき・疑問：
  - `app/mcp_agent.py` は一切変えず、`app/mcp_servers.json` を書き足しただけで、見えるツールが 1 個 → 2 個 → 7 個と増えた。エージェントが起動のたびにサーバーへツールの一覧を問い合わせている（講義 Part 2 の tools/list）ことが、表示で確かめられた
  - STEP 3 は「3行に要約して」と頼んだだけなのに、fetch のあとで `glossary_search_glossary({'query': 'MCP'})` も呼び、回答の最後に「第3回・第6回」と付けた。STEP 2 でも「関連する回：第1回」と付けていたので、指示文が用語集を引くように書かれているためと考えているが、未確認
  - fetch_fetch の引数には、`url` のほかに `max_length`（既定 5000）や `raw` などもあったが、モデルは `url` だけを指定していた
  - 503 が STEP 2 と STEP 4 で 1 回ずつ出て、そのまま終了した。再実行すると通った
  - 最初は `No module named app.mcp_agent` と出た。`ls app/` で `mcp_agent.py` がないことを確認し、`git fetch upstream` → `git merge upstream/main` で第6回の更新を取り込んで解決した。Sync fork をしていなかったのが原因だった

## 宿題

<!-- 基礎・実装・発展のどれか1つに取り組めば完了です。 -->

- 取り組んだレベル：発展（Claude Code）
- やったこと：
  - 調べた日：2026-11-25
  - 対象：Claude Code 2.1.332（普段使っているもの）
  - 参照した公式ドキュメント
    - https://code.claude.com/docs/en/mcp
    - https://code.claude.com/docs/en/settings
  - ドキュメントを読んだうえで、手元の Claude Code で実際に確かめた
    - `claude mcp add --help` で、コマンドの書き方と、スコープの既定値を確認した
    - 演習の STEP 3・4 と同じ fetch サーバーと AWS サーバーを、テスト用のフォルダで `claude mcp add` を使って追加し、どのファイルに何が書かれるかを見た（local・project・user の 3 つのスコープ。確かめたあと削除した）
    - 演習と同じ `{"url": "..."}` だけの書き方が通るかを、`claude mcp add-json` で試した
  - 演習（Codespaces）での `--list-tools` と `--trace` の出力と比べた
- 結果：

### 1. 設定を書く場所
| | 演習 | Claude Code |
|---|---|---|
| ファイル | `app/mcp_servers.json` | スコープによって違う（下の 4.） |
| 書き方 | ファイルを手で編集する | `claude mcp add` コマンドで追加するのが基本。`.mcp.json` は手で書いてもよい。Claude Code の中では `/mcp` で状態の確認や認証もできる |
| 一番外側のキー | `"mcpServers"` | 同じ `"mcpServers"` |

### 2. コマンドで起動する書き方（演習の `"command"`）
演習の STEP 3 で書き足した fetch サーバー：
```json
"fetch": {
  "command": "uvx",
  "args": ["mcp-server-fetch==2026.11.11", "--no-readability-js"]
}
```
同じサーバーを Claude Code で追加したときのコマンド：
```
claude mcp add -s project fetch -- uvx mcp-server-fetch==2026.11.11 --no-readability-js
```
`.mcp.json` に書かれた内容（実際の出力）：
```json
"fetch": {
  "type": "stdio",
  "command": "uvx",
  "args": ["mcp-server-fetch==2026.11.11", "--no-readability-js"],
  "env": {}
}
```
- `command` と `args` は演習とまったく同じ。Claude Code は `"type": "stdio"` と `"env"` も書き足した（ドキュメントによると、`type` を省くと stdio として扱われる）
- `--` より後ろが、サーバーを起動するコマンドとしてそのまま渡る。環境変数は `-e KEY=value` で渡せる
- `.mcp.json` の中では `${VAR}` や `${VAR:-既定値}` で環境変数を展開できる。API キーをファイルに直接書かなくて済む

### 3. URL で接続する書き方（演習の `"url"`）
演習の STEP 4 では、次の 1 行で AWS のサーバーに接続でき、`[server] aws: URL に接続（https://knowledge-mcp.global.api.aws）` と表示された。
```json
"aws": {"url": "https://knowledge-mcp.global.api.aws"}
```
Claude Code で同じものを追加するときのコマンドと、書かれた内容：
```
claude mcp add -s project --transport http aws https://knowledge-mcp.global.api.aws
```
```json
"aws": {
  "type": "http",
  "url": "https://knowledge-mcp.global.api.aws"
}
```
- **演習との一番大きな違い**：演習の書き方（`url` だけ）をそのまま Claude Code に渡すと、次のエラーで追加できなかった。Claude Code では `"type"` が必須
  `Invalid configuration: it has a "url" but no "type". Add "type": "http" (or "sse" / "ws").`
- `type` には `http`（推奨）、`sse`（非推奨）、`ws` がある。SSE は非推奨で、HTTP を使うよう書かれている
- 認証が必要なサーバーには、`--header "Authorization: Bearer ..."` でヘッダーを付けるか、`/mcp` や `claude mcp login` で OAuth の認証をする。演習の AWS Knowledge サーバーは認証が不要だった

### 4. 有効になる範囲（スコープ）
| スコープ | 保存先（実際に確かめた） | 有効になる範囲 |
|---|---|---|
| local（**既定**） | `~/.claude.json` の、そのプロジェクトの項目の中 | そのプロジェクトだけ。自分だけ |
| project | プロジェクト直下の `.mcp.json` | そのプロジェクトだけ。Git に入れればチームで共有できる |
| user | `~/.claude.json` の一番外側の `mcpServers` | 自分のすべてのプロジェクト |

- 同じ名前のサーバーが複数のスコープにあるときは、local、project、user の順に優先される（ドキュメントより。自分では試していない）
- project スコープのサーバーは、最初に使う前に承認を求められる。`claude mcp get aws` を実行すると、`Status: ⏸ Pending approval` と表示された
- 演習の `app/mcp_servers.json` は、リポジトリに入っていて、そのリポジトリでだけ有効になるので、project スコープ（`.mcp.json`）に近い。ただし承認の手順はなく、書き足すとすぐに起動・接続された

### 5. ツールの名前
| | 演習（実際の表示） | Claude Code |
|---|---|---|
| 形 | `サーバー名_ツール名` | `mcp__サーバー名__ツール名` |
| 例 | `glossary_search_glossary`、`fetch_fetch`、`aws_aws___search_documentation` | `mcp__glossary__search_glossary` など（ドキュメントの形に当てはめたもの。自分では表示させていない） |

- 演習の `aws_aws___search_documentation` は、サーバー名 `aws` と、AWS 側のツール名 `aws___search_documentation` をつないだもの。区切りの `_` が 1 つだけなので、どこまでがサーバー名か見分けにくい。Claude Code は `mcp__` と `__` で区切るので、見分けやすい

### 6. ツールの渡し方（ツール検索）
- 演習のエージェントは、起動時に全サーバーのツールをすべてモデルに渡す。STEP 4 では `モデルに見えているツール: 7 個` で、AWS のツールは 1 つ 1 つの説明文がとても長かった
- 演習の `[usage]` の入力トークンは、glossary だけのとき（STEP 2）が 715 tokens、aws を足したとき（STEP 4）が 6,359 tokens だった（どちらもツールの結果を含むので、ツールの定義だけの量ではない）
- Claude Code では、ツール検索が既定で有効。MCP のツールは最初からすべて渡されるのではなく、必要になったときに検索して読み込まれる（`ENABLE_TOOL_SEARCH` で変えられる）。講義 Part 3 の「ツール検索」の仕組みが、既定で入っている
- 出力の上限：Claude Code では、MCP ツールの出力は既定で 2.5 万トークンまで（`MAX_MCP_OUTPUT_TOKENS` で変えられる。ドキュメントより）

- 気づき・疑問：
  - `mcpServers`・`command`・`args`・`url` の形は演習と同じで、演習の設定はほぼそのまま Claude Code に持っていけた。違いは、URL で接続するとき `"type": "http"` が必須なことだった。演習の書き方で追加すると失敗したが、エラーメッセージに「`"type": "http"` を足す」と直し方まで書かれていたので、すぐ直せた。講義 Part 3 の「エラーには、どの引数をどう直せばよいかを書く」の実例になっていた
  - 演習の `app/mcp_servers.json` はリポジトリに入れて共有する点で Claude Code の project スコープ（`.mcp.json`）に近いが、Claude Code は `.mcp.json` のサーバーを承認するまで起動しない（`⏸ Pending approval`）。演習は書けばすぐ起動した。他人が書いた設定ファイルのコマンドを、clone しただけで実行してしまわないための違いだと思った
  - fetch の説明文には「もともとはインターネットにアクセスできなかったが、このツールでアクセスできるようになった」という、モデルへの指示のような文があった。説明文はそのままモデルに渡るので、サーバーを足すことは、指示文の一部をサーバーの作者に書かせることでもある。演習の補足の「足す前に、提供元を確認する」は、コマンドの実行だけでなく、説明文の中身にも当てはまると思った
  - サーバーを 3 つにしただけで、ツールは 7 個になった。AWS のツールは説明文が特に長く、入力トークンは STEP 2 の 715 から STEP 4 の 6,359 に増えた。ただし、どちらもツールの結果を含むので、ツールの定義だけでどれだけ増えたかは区別できていない。Claude Code がツール検索を既定で有効にしているのは、この増え方を避けるためだと考えた
  - ツール名は、演習では `aws_aws___search_documentation` のように `_` 1 つでつなぐので、どこまでがサーバー名か読みにくかった。Claude Code の `mcp__aws__…` の方が区切りがはっきりしている（Claude Code 側の実際の名前は、自分では表示させていない）
  - 疑問：演習のエージェントにツール検索を入れると、入力トークンはどれくらい減るのか。また、検索で候補を絞ると、正しいツールを選べる割合は上がるのか、下がるのか（講義 Part 3 の GitHub Copilot の事例では上がっていた）
