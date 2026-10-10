"""データ取得と分類パイプラインのCLIを提供する。"""

import argparse
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

from instagram_analysis.decisions import classify_post
from instagram_analysis.drive_data import data_dir, sync_drive_data
from instagram_analysis.instagram import load_posts
from instagram_analysis.storage import save_results


def main() -> None:
    """引数を読み取り、データ取得または分類・保存を実行する。

    Raises:
        ValueError: 入力CSVまたはAPI設定が不正な場合。
        OSError: データファイルを読み書きできない場合。
        openai.APIError: 分類APIとの通信に失敗した場合。
    """
    load_dotenv(Path.cwd() / ".env", override=False)
    parser = argparse.ArgumentParser(description=__doc__)
    subcommands = parser.add_subparsers(dest="command", required=True)
    subcommands.add_parser("download", help="Driveからデータを取得")
    classify = subcommands.add_parser("classify", help="投稿CSVを分類して保存")
    classify.add_argument("--input", type=Path, required=True)
    classify.add_argument("--output", type=Path, required=True)
    classify.add_argument("--limit", type=int, default=10)
    classify.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "download":
        paths = sync_drive_data()
        print(f"{len(paths)}個のファイルを{data_dir()}に取得しました")
        return
    if args.limit < 1:
        parser.error("--limitは1以上を指定してください。")
    posts = load_posts(args.input)[: args.limit]
    if args.dry_run:
        print(f"入力確認完了: {len(posts)}件。API呼び出しはありません。")
        return
    if not os.environ.get("OPENAI_API_KEY", "").strip():
        raise ValueError(".envまたは環境変数にOPENAI_API_KEYが必要です。")
    model = os.environ.get("OPENAI_MODEL", "gpt-6-luna")
    with OpenAI(timeout=60.0, max_retries=2) as client:
        results = (classify_post(client, post, model) for post in posts)
        count = save_results(results, args.output)
    print(f"{count}件の分類結果を{args.output}に保存しました")


if __name__ == "__main__":
    main()
