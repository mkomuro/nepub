# nepub

> [!NOTE]
> こちらは自分用 (mkomuro) の開発／テスト版ブランチ。

「小説家になろう」および「カクヨム」の小説を縦書きの EPUB に変換するためのツール

## Requirements

- Python 3
  - 3.12 ~~3.10~~ で動作確認しています

## Installation
**main ブランチ:** なるべくフォーク元を維持する予定
```sh
pip install git+https://github.com/mkomuro/nepub.git
```

**dev ブランチ:** 自分用なので main にマージしないかもしれない
```sh
pip install git+https://github.com/mkomuro/nepub.git@dev
```
あるいは
```sh
git clone -b dev https://github.com/mkomuro/nepub.git nepub-dev
pip install --no-cache-dir -e nepub-dev
```


## Usage

```sh
$ nepub -h
usage: nepub [-h] [-i] [-t] [-r <range>] [-o <file>] [-k] [-c [<jpeg_file>]] novel_id

positional arguments:
  novel_id              novel id

options:
  -h, --help            show this help message and exit
  -i, --illustration    Include illustrations (Narou only)
  -t, --tcy             Enable Tate-Chu-Yoko conversion
  -r <range>, --range <range>
                        Specify the target episode number range using
                        comma-separated values (e.g., "1,2,3") or a range notation (e.g., "10-20").
  -o <file>, --output <file>
                        Output file name. If not specified, ${novel_id}.epub is used.
                        Update the file if it exists.
  -k, --kakuyomu        Use Kakuyomu as the source
  -c [<jpeg_file>], --cover [<jpeg_file>]
                        Insert a cover JPEG image in the EPUB file (optional: specify filename)
```

Example:

```sh
$ nepub xxxx
novel_id: xxxx, illustration: False, tcy: False, output: xxxx.epub, kakuyomu: False
cover_jpeg: None
xxxx.epub found. Loading metadata for update.
3 episodes found.
Start downloading...
Download skipped (already up to date) (1/3): https://ncode.syosetu.com/xxxx/1/
Download skipped (already up to date) (2/3): https://ncode.syosetu.com/xxxx/2/
Downloading (3/3): https://ncode.syosetu.com/xxxx/3/
Download is complete! (new: 1, skipped: 2)
Updated xxxx.epub.
```

※ xxxx の部分には小説ページの URL の末尾部分 (`https://ncode.syosetu.com/{ここの文字列}/`) に置き換えてください。

## 自分用 nepub の変更点 (Upstream との違い)
### 連続する空行の処理
空行が連続する場合の処理を変更しました。
|自分用 (`dev`ブランチ)|Upstream 版 (`main`ブランチ)|
|:-:|:-:|
|1 行 &rarr; 1 行|1 行 &rarr; 削除|
|2 行以上 &rarr; 2 行|2 行以上 &rarr; 1 行|

### 表紙画像を挿入
自分が使用している一部の EPUB ビューワーソフトが EPUB 本文に含まれている挿絵の画像ファイルをアイコン画像として「本棚」機能でサムネイル表示してしまうため、表紙画像を EPUB ファイルに挿入する機能を追加しました。

```sh
# -c [<jpeg_file>], --cover [<jpeg_file>]
#     Insert a cover JPEG image in the EPUB file (optional: specify filename)

nepub -i -t -c <novel_id>
```

`-c` オプションで下記のサンプル画像のような表紙を挿入します。表紙の「タイトル」と「作者名」は Web から取得したのものがそのまま埋め込まれます。

<!-- ![サンプルの表紙画像](./assets/size-A6-short-cover.jpg) -->
<p align="center">
<img src="./assets/size-A6-short-cover.jpg" alt="サンプルの表紙画像" style="width: 40%; height: auto;">
</p>

加えて、`-c` に続いてローカルパスにある「JPEG 画像ファイル名」を指定すると、そのファイルを表紙画像として EPUB ファイルに挿入します。
```sh
nepub -i -t -c <jpeg_file> <novel_id>
```

生成されるデフォルトの JPEG 表紙画像には、以下の属性が設定されています。画像サイズなどの属性を変更したい場合は、コード側の修正が必要です。
```sh
# A6 (300dpi) 相当を期待したピクセル数
$ file -b size-A6-short-cover.jpg | tr ',' '\n'
JPEG image data
 JFIF standard 1.01
 aspect ratio
 density 1x1
 segment length 16
 baseline
 precision 8
 1240x1748
 components 3
```

#### 任意の「タイトル名」と「作者名」を埋め込んだ表紙画像の生成
任意の「小説タイトル」や「作者名」を埋め込んだ JPEG 表紙画像を、事前に生成することができます。以下は、上記のサンプルと同じ JPEG 表紙画像を生成する際のコマンド例です。
```sh
# nepub.cover "novel_title" "novel_author" "jpeg_filename" "A6 | B6 | KINDLE"
#   A6 (文庫 = 1:1.41)
#       width:   1240 = (105mm / 25.4) * 300dpi
#       height:  1748 = (148mm / 25.4) * 300dpi
#   B6 (単行本 = 1:1.42)
#       width:   1512 = (128mm / 25.4) * 300dpi
#       height:  2150 = (182mm / 25.4) * 300dpi
#   KINDLE (1:1.41): https://kdp.amazon.co.jp/ja_JP/help/topic/G6GTK3T3NUHKLEFX
#       width:   1816 px
#       height:  2560 px

python -m nepub.cover \
    "小説のタイトル名" \
    "小説の作者名" \
    "size-A6-short-cover.jpg" \
    "A6"
```

生成した JPEG 表紙画像を `-c` オプションの引数として指定すると、その画像が EPUB ファイルの表紙として挿入されます。
```sh
nepub -i -t -c "size-A6-short-cover.jpg" -o "小説のタイトル名.epub" <novel_id>
```

## 免責事項

> [!NOTE]
> 免責事項、ライセンスなどは、フォーク元のレポジトリと同様です。フォーク元と本レポジトリの同期がずれた場合でも（同期が遅れてしまった場合でも）基本的にはフォーク元に従うようにしますのでフォーク元のレポジトリも同時に参照してください。

本ツールは、小説投稿サイト「小説家になろう」および「カクヨム」の小説を縦書きの EPUB に変換するための非公式ツールです。
本ツールは株式会社ヒナプロジェクトおよび株式会社 KADOKAWA とは一切関係がありません。

「小説家になろう」は、株式会社ヒナプロジェクトの登録商標です。
「カクヨム」は、株式会社 KADOKAWA の登録商標です。

### 注意事項

* 自分用に作成したため、最低限読める EPUB を出力する機能しかありません
* 「小説家になろう」および「カクヨム」のサーバーに負荷をかけないよう、ご注意ください
* 本ツールの使用によって生じたいかなる結果についても責任を負いません。ご使用は自己責任でお願いいたします。
