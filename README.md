# AIPlomo / Instagram Analysis

2人で開発するInstagram投稿分析プロジェクトです。1つのリポジトリで、
データ取得・OpenAI Decisions APIによる分類・結果保存を管理します。
将来のML用ディレクトリは、必要になった時点で追加します。

## 現在できること

- 公開共有されたGoogle Driveフォルダからデータを取得。
- UTF-8の投稿CSVを検証し、投稿本文から企業／個人と想定読者年齢層を分類。
- 投稿ID・判定日時・モデル・分類基準バージョン・元データをCSVへ保存。
- APIを呼ばない入力確認、uvによる環境再現、RuffのCIチェック。

画像の分類、Instagram APIからの直接取得、Parquet保存、ML学習は未実装です。
Drive内の実データ形式はまだ確認できていないため、以下の入力CSV形式に
合わせてから使用してください。実データや秘密情報はGitHubへ保存しません。

## 構成

```text
AIPlomo/
├── src/instagram_analysis/
│   ├── __init__.py
│   ├── main.py          # CLI・処理の順序
│   ├── drive_data.py    # Google Driveからの取得
│   ├── instagram.py     # CSV読み込み・入力検証
│   ├── decisions.py     # 分類基準・Decisions APIの呼び出し
│   └── storage.py       # 分類結果のCSV保存
├── tests/              # 重要な処理のテストを追加する場所
├── notebooks/          # 分析・検証用
├── data/               # Git管理外。実行時に作成
│   ├── raw/
│   └── processed/
├── .github/workflows/ci.yml
├── .env.example
├── .python-version
├── pyproject.toml
├── uv.lock
├── Dockerfile
├── .dockerignore
├── drive_data.py        # 従来コマンドの互換用
├── CODE_PATTERNS.md
└── README.md
```

設計の理由と変更例は [CODE_PATTERNS.md](./CODE_PATTERNS.md) を参照してください。

## 環境構築

Python 3.12と[uv](https://docs.astral.sh/uv/getting-started/installation/)を使います。
リポジトリのルートで実行します。uvが必要なPythonと `.venv` を準備します。

```sh
uv sync --locked
```

初回のみ [.env.example](./.env.example) を `.env` にコピーして設定します。
**既存の `.env` がある場合は上書きせず、不足項目だけ追加してください。**

| 環境変数 | 用途・既定値 |
| --- | --- |
| `OPENAI_API_KEY` | 分類実行に必要。取得・入力確認・Ruffでは不要 |
| `OPENAI_MODEL` | `gpt-6-luna` |
| `GOOGLE_DRIVE_FOLDER_URL` | 提示された共有フォルダURL |
| `GOOGLE_DRIVE_DATA_DIR` | `data/raw` |

CLIはカレントディレクトリの `.env` を読み込みます。
OSの環境変数が優先されます。ライブラリとして呼ぶ場合は呼び出し側で
環境変数を設定してください。旧 `.env.sample` は `.env.example` に統一しました。

## データを取得する

Driveの公開共有フォルダを使う場合は「リンクを知っている全員」が閲覧できる
設定にしてから実行します。非公開共有フォルダの認証取得は未対応です。

```sh
uv run instagram-analysis download
```

既定の保存先は `data/raw/` です。以前の `.drive_data/` を使い続ける場合は
`GOOGLE_DRIVE_DATA_DIR=.drive_data` を設定してください。
同期は取得・更新を行いますが、Driveから削除されたファイルをローカルから
削除する完全なミラー同期ではありません。

従来の `uv run python drive_data.py` も使用できます。

## 投稿CSVの形式

必須列は `post_id` と `text` です。IDは空でない一意の文字列として扱い、
先頭のゼロを保持します。UTF-8 BOM付きCSVにも対応します。

```csv
post_id,text
sample-001,当店の新商品を紹介します。
sample-002,週末に友達と散歩しました。
```

任意の追加列は結果の `post_json` に保持しますが、現在APIへ送るのは
`text` のみです。本文とIDの前後の空白を除き、空値や重複IDを拒否します。
元CSVは変更しません。実際のDrive内のファイル名に合わせて入力パスを変更してください。

## 分類と保存

最初はAPIを呼ばずに入力形式を確認します。

```sh
uv run instagram-analysis classify \
  --input data/raw/posts.csv \
  --output data/processed/results-001.csv \
  --dry-run
```

分類を実行する場合は `--dry-run` を外します。API利用料金が発生します。
既定の処理件数は先頭10件で、`--limit` で指定できます。

```sh
uv run instagram-analysis classify \
  --input data/raw/posts.csv \
  --output data/processed/results-001.csv \
  --limit 10
```

出力ファイルは新規作成のみです。同名ファイルがあればAPIを呼ぶ前に停止します。
結果は1投稿ずつ保存するため、途中で通信エラーになっても成功分が残ります。
自動再開は未実装です。再実行時は保存済みIDを入力から除き、別の出力名を指定します。

### 保存する情報

| 列 | 内容 |
| --- | --- |
| `post_id`, `post_json` | 元投稿IDと入力CSVの各列（前後空白除去後） |
| `classified_at` | UTCの判定日時 |
| `requested_model`, `model` | 指定モデルとAPI応答のモデル |
| `criteria_version` | 分類基準バージョン。初期値 `v1` |
| `input_sha256` | APIへ渡した本文のSHA-256 |
| `account_type`, `target_age` | 発信主体と想定読者年齢層 |
| `*_status`, `*_confidence` | 回答種別とAPIが返す信頼度 |
| `request_id`, `decision_json` | APIリクエストID（取得できた場合）と応答全体 |

分類結果は機械による推定です。`unknown`は根拠不足を示し、APIによる
判定拒否は `*_status=refusal` として分け、分類値を空にします。
年齢層は投稿の想定読者を対象にし、投稿者や写真の人物の年齢を推定しません。
分類基準の意味と区分は2人で確認し、変更時はバージョンを更新してください。

[公式Decisions APIガイド](https://developers.openai.com/api/docs/guides/decisions)に
沿って実装しています（2026-10-10確認、SDK 3.26.0以上）。
APIへの実接続と実データでの分類品質評価は、別途行う必要があります。

## 2人での開発

1. Issueで目的、担当、完了条件を決める。
2. 最新の `main` から `feature/instagram-ingestion` などのブランチを作る。
3. 実装とドキュメントを更新し、Ruffを実行する。
4. PRに変更内容・確認方法・残課題を書く。
5. 相手がレビューし、CI成功後に `main` へマージする。

```sh
uv run ruff check .
uv run ruff format --check .
# 自動整形
uv run ruff format .
# 依存追加（pyproject.tomlとuv.lockを両方コミット）
uv add パッケージ名
uv add --dev 開発用パッケージ名
```

GitHub ActionsはRuffのlintと整形のみです。APIキーや実データはCIに不要です。
重要な処理にpytestを導入する時点で、CIにもテストを追加します。
GitHubのブランチ保護でPRレビュー1名とCI成功を必須にする運用を推奨します。
リモートのブランチ保護設定自体は、このリポジトリでは変更していません。

## Docker

イメージにはコードと固定した依存関係を含めます。秘密情報とデータは実行時に渡します。

```sh
docker build -t aiplomo .
mkdir -p data/raw data/processed
docker run --rm --env-file .env -v "$(pwd)/data:/app/data" \
  aiplomo download
docker run --rm --env-file .env -v "$(pwd)/data:/app/data" \
  aiplomo classify --input data/raw/posts.csv \
  --output data/processed/results-001.csv --limit 10
```

## 将来の拡張

- 前処理が増えたら `preprocessing.py`、複数の取得元が増えたら `ingestion/` に分割。
- Parquetが必要になったら保存モジュールへ追加し、必要な依存だけ導入。
- 特徴量生成や学習を始めたら `features/` と `ml/` を追加。
- APIの予測と人の確定ラベルは分け、投稿ID・分類基準・入力ハッシュで追跡する。
- Notebookで固まった処理はPythonモジュールへ移す。

`.env`、`.venv/`、`data/`、エージェント設定はGit管理外です。
