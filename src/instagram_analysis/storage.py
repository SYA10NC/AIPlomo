"""分類結果を上書きせず、投稿ごとにCSVへ保存する。"""

import csv
from collections.abc import Iterable
from pathlib import Path

FIELDS = [
    "post_id",
    "classified_at",
    "requested_model",
    "model",
    "criteria_version",
    "input_sha256",
    "post_json",
    "request_id",
    "account_type",
    "account_type_status",
    "account_type_confidence",
    "target_age",
    "target_age_status",
    "target_age_confidence",
    "decision_json",
]


def save_results(results: Iterable[dict[str, str]], path: Path) -> int:
    """結果を新しいCSVへ順次書き込み、保存件数を返す。

    Args:
        results: 投稿ごとの分類結果。ジェネレーターも指定できる。
        path: 新規に作成するCSVファイルのパス。

    Returns:
        正常に保存した投稿数。

    Raises:
        FileExistsError: 出力ファイルが既に存在する場合。
        ValueError: 出力先の拡張子が.csv以外の場合。
        OSError: ファイルを書き込めない場合。
    """
    if path.suffix.lower() != ".csv":
        raise ValueError("出力ファイルには.csvを指定してください。")
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("x", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for result in results:
            writer.writerow(result)
            stream.flush()
            count += 1
    return count
