#!/usr/bin/env python3
import sys
sys.dont_write_bytecode = True

import argparse
import csv
import os
import subprocess
import shlex
from pathlib import Path

def main():
    # --- 引数の解析 (argparse) ---
    parser = argparse.ArgumentParser(
        description="CSV ファイルの情報を読み込み、nepub を実行して EPUB ファイルを作成する。"
    )
    parser.add_argument(
        "csv_files", 
        nargs='+',
        help="入力CSVファイル名（1つ以上指定可能）"
    )
    parser.add_argument(
        "-d", "--dir", 
        default="./epub_data/",
        help="EPUBファイルの出力先フォルダ (デフォルト: ./epub_data/)"
    )
    
    args = parser.parse_args()

    epub_dir = Path(args.dir)

    # 出力先ディレクトリの作成 (n と k サブフォルダを含む)
    try:
        (epub_dir / "n").mkdir(parents=True, exist_ok=True)
        (epub_dir / "k").mkdir(parents=True, exist_ok=True)
    except Exception as e:
        print(f"Error: 出力先ディレクトリ '{epub_dir}' の作成に失敗しました: {e}")
        sys.exit(1)

    # 処理に成功したCSVファイルの数をカウント
    processed_count = 0

    # --- 各CSVファイルのループ処理 ---
    for csv_file in args.csv_files:
        csv_path = Path(csv_file)

        # --- バリデーション ---
        if not csv_path.exists():
            print(f"Error: CSVファイル '{csv_path}' が見つかりません。スキップします。")
            continue

        print(f"\n>>> 処理中: {csv_path}")

        # --- CSVファイルの読み込みと処理 ---
        try:
            with csv_path.open(mode='r', encoding='utf-8', newline='') as f:
                reader = csv.reader(f)
                
                # ファイルが正常に開け、中身の処理を開始したことをカウント
                processed_count += 1
                
                for row in reader:
                    # 空行またはコメント行 (# で始まる) をスキップ
                    if not row or not row[0] or row[0].startswith('#'):
                        continue

                    # 各列の取得 (Bashスクリプトのparam1, param2, param3に相当)
                    # 万が一列が足りない場合のためにデフォルト値を設定
                    col1 = row[0].strip()
                    col2 = row[1].strip() if len(row) > 1 else ""
                    col3 = row[2].strip() if len(row) > 2 else ""

                    # --- コマンド組み立て ---
                    if col1[0].isalpha():
                        # 小説IDが英字で始まる場合 (なろう)
                        base_cmd = ["nepub", "-i"]
                        sub_folder = "n"
                        output_filename = f"{col2}_{col1}.epub"
                    else:
                        # 小説IDが数字で始まる場合 (カクヨム)
                        base_cmd = ["nepub", "-k"]
                        sub_folder = "k"
                        output_filename = f"{col2}_kakuyomu.epub"

                    output_path = epub_dir / sub_folder / output_filename

                    # コマンドリストの構築
                    full_command = base_cmd.copy()
                    
                    # col3 (オプション) がある場合、スペースで分割して追加
                    if col3:
                        # shlex.splitを使うことで、"-r 284-288"のような引数を適切にリスト化します
                        full_command.extend(shlex.split(col3))

                    # 出力先の追加
                    if col2:
                        full_command.extend(["-o", str(output_path)])

                    # 最後に小説IDを追加
                    full_command.append(col1)

                    # --- 実行 ---
                    print(f"  RUN> {' '.join(full_command)}")
                    
                    try:
                        # コマンドの実行
                        subprocess.run(full_command, check=True)
                        # 権限変更 (644)
                        if output_path.exists():
                            os.chmod(output_path, 0o644)
                    except subprocess.CalledProcessError as e:
                        print(f"  Error: コマンドの実行に失敗しました: {e}")
                    except FileNotFoundError:
                        print("  Error: 'nepub' コマンドが見つかりません。パスが通っているか確認してください。")

        except Exception as e:
            print(f"  Error: ファイル '{csv_path}' の処理中にエラーが発生しました: {e}")

    # --- 終了処理 ---
    # 【対応2】1つも処理できなかった場合のメッセージ
    if processed_count == 0:
        print("\n" + "!" * 60)
        print("エラー: 指定されたCSVファイルの中に、正常に処理できたものがありませんでした。")
        print("!" * 60)
        sys.exit(1)

    print(f"\nすべてのタスクが完了しました。EPUBファイルは '{epub_dir}' 内にあります。")
    
    # 最後にツリー表示 (システムにtreeコマンドがある場合)
    try:
        subprocess.run(["tree", "-h", str(epub_dir)])
    except FileNotFoundError:
        #print(f"(treeコマンドが未インストールのため一覧表示をスキップします)")
        pass

if __name__ == "__main__":
    main()
