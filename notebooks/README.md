# 分析・検証用Notebook

必要になった段階でNotebookを追加します。再利用する処理は
[src/instagram_analysis](../src/instagram_analysis/)へ移してください。

実データと分析結果はGit管理外の `data/` に保存します。
Notebookをコミットするときは、投稿本文や画像、秘密情報を含む出力を消し、
実行に必要な依存関係を `uv add --dev` で登録してください。
