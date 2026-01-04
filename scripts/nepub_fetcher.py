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
        description="CSVファイルの情報を読み込み、nepubを実行してEPUBファイルを作成するスクリプト。"
    )
    parser.add_argument(
        "-c", "--csv", 
        default="./fetch-list_sample.csv",
        help="入力CSVファイル名 (デフォルト: ./fetch-list_sample.csv)"
    )
    parser.add_argument(
        "-d", "--dir", 
        default="./epub_data/",
        help="EPUBファイルの出力先フォルダ (デフォルト: ./epub_data/)"
    )
    
    args = parser.parse_args()

    csv_path = Path(args.csv)
    epub_dir = Path(args.dir)

    # --- バリデーション ---
    if not csv_path.exists():
        print(f"Error: 指定されたCSVファイル '{csv_path}' が見つかりません。")
        return

    # 出力先ディレクトリの作成 (n と k サブフォルダを含む)
    (epub_dir / "n").mkdir(parents=True, exist_ok=True)
    (epub_dir / "k").mkdir(parents=True, exist_ok=True)

    # --- CSVファイルの読み込みと処理 ---
    # newline='' を指定することで、Pythonが自動的にLF/CRLFの変換をハンドルします
    try:
        with csv_path.open(mode='r', encoding='utf-8', newline='') as f:
            # csv.readerはデフォルトで引用符(")の除去も行います
            reader = csv.reader(f)
            
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
                    base_cmd = ["nepub", "-i", "-t"]
                    sub_folder = "n"
                    output_filename = f"{col2}_{col1}.epub"
                else:
                    # 小説IDが数字で始まる場合 (カクヨム)
                    base_cmd = ["nepub", "-k", "-t"]
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
                print(f"RUN> {' '.join(full_command)}")
                
                try:
                    # コマンドの実行
                    subprocess.run(full_command, check=True)
                    
                    # 権限変更 (644)
                    if output_path.exists():
                        os.chmod(output_path, 0o644)
                except subprocess.CalledProcessError as e:
                    print(f"Error: コマンドの実行に失敗しました: {e}")
                except FileNotFoundError:
                    print("Error: 'nepub' コマンドが見つかりません。パスが通っているか確認してください。")

    except Exception as e:
        print(f"Error: ファイルの処理中にエラーが発生しました: {e}")

    # --- 終了処理 ---
    print(f"\nすべてのタスクが完了しました。EPUBファイルは '{epub_dir}' 内にあります。")
    
    # 最後にツリー表示 (システムにtreeコマンドがある場合)
    try:
        subprocess.run(["tree", "-h", str(epub_dir)])
    except FileNotFoundError:
        print(f"(treeコマンドが未インストールのため一覧表示をスキップします)")

if __name__ == "__main__":
    main()
