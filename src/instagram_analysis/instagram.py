"""エクスポートされたInstagram投稿CSVを読み込む。"""

import csv
from pathlib import Path


def load_posts(path: Path) -> list[dict[str, str]]:
    """投稿IDと本文を検証し、投稿一覧を読み込む。

    Args:
        path: post_idとtext列を持つUTF-8のCSVファイル。

    Returns:
        前後の空白を除いた投稿の辞書一覧。追加列も保持する。

    Raises:
        ValueError: 必須列や値が欠落、または投稿IDが重複している場合。
        OSError: 入力ファイルを読み込めない場合。
    """
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not {"post_id", "text"}.issubset(reader.fieldnames or []):
            raise ValueError("CSVにはpost_idとtext列が必要です。")
        posts = []
        seen = set()
        for line, row in enumerate(reader, start=2):
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"CSVの{line}行目の列数が不正です。")
            post = {key: value.strip() for key, value in row.items()}
            if not post["post_id"] or not post["text"]:
                raise ValueError(f"CSVの{line}行目のIDまたは本文が空です。")
            if post["post_id"] in seen:
                raise ValueError(f"CSVの{line}行目の投稿IDが重複しています。")
            seen.add(post["post_id"])
            posts.append(post)
    if not posts:
        raise ValueError("CSVに投稿がありません。")
    return posts
