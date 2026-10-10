"""Google Drive上の共有フォルダからデータを取得して参照する。"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

DEFAULT_FOLDER_URL = (
    "https://drive.google.com/drive/folders/1ZkZNH6U8cr-Gnc9sMUbjesmy4WBnDMbf"
)


def data_dir() -> Path:
    """データのキャッシュ先ディレクトリを返す。

    Returns:
        キャッシュ先の絶対パス。
    """
    return Path(os.environ.get("GOOGLE_DRIVE_DATA_DIR", "data/raw")).resolve()


def sync_drive_data(*, quiet: bool = False) -> list[Path]:
    """共有Driveフォルダをローカルキャッシュへ同期する。

    Args:
        quiet: Trueの場合、ダウンロードの進捗を表示しない。

    Returns:
        ダウンロードされたファイルのパス一覧。

    Raises:
        RuntimeError: gdownが未導入、またはフォルダを取得できない場合。
    """
    try:
        import gdown
    except ImportError as exc:
        raise RuntimeError(
            "gdownが必要です。`uv sync`で依存関係をインストールしてください。"
        ) from exc

    folder_url = os.environ.get(
        "GOOGLE_DRIVE_FOLDER_URL", DEFAULT_FOLDER_URL
    ).strip()
    destination = data_dir()
    destination.mkdir(parents=True, exist_ok=True)
    downloaded: list[str] | None = gdown.download_folder(
        url=folder_url,
        output=str(destination),
        quiet=quiet,
        use_cookies=False,
    )
    if downloaded is None:
        raise RuntimeError(
            "Google Driveフォルダを取得できませんでした。"
            "リンクを知っている全員に閲覧権限があることと、"
            "フォルダURLを確認してください。"
        )
    return [Path(path) for path in downloaded]


def get_data_path(relative_path: str | Path, *, sync: bool = True) -> Path:
    """Driveデータ内のファイルパスを返す。

    Args:
        relative_path: Driveフォルダからの相対パス。
        sync: Trueの場合、パスを返す前にDriveを同期する。

    Returns:
        指定されたファイルの絶対パス。

    Raises:
        ValueError: 相対パスがデータディレクトリの外を指す場合。
        FileNotFoundError: 指定されたファイルが存在しない場合。
        RuntimeError: Driveフォルダを同期できない場合。
    """
    root = data_dir().resolve()
    target = (root / relative_path).resolve()
    if target != root and root not in target.parents:
        raise ValueError(
            "relative_path must stay inside the Drive data directory"
        )
    if sync:
        sync_drive_data(quiet=True)
    if not target.is_file():
        raise FileNotFoundError(f"Drive data file not found: {target}")
    return target


def main() -> None:
    """コマンドラインからDriveデータを同期する。

    Returns:
        None。
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="ダウンロードの進捗を表示しない",
    )
    args = parser.parse_args()
    paths = sync_drive_data(quiet=args.quiet)
    print(f"{len(paths)}個のファイルを{data_dir()}に取得しました")


if __name__ == "__main__":
    main()
