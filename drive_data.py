"""従来のDrive取得コマンドとインポートに互換性を提供する。"""

from pathlib import Path

from dotenv import load_dotenv

from instagram_analysis.drive_data import (
    data_dir,
    get_data_path,
    main,
    sync_drive_data,
)

__all__ = ["data_dir", "get_data_path", "main", "sync_drive_data"]

if __name__ == "__main__":
    load_dotenv(Path.cwd() / ".env", override=False)
    main()
