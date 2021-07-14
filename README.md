# multiple-renamer
本ツールは、複数のファイルを一括でリネームすることができるツールです。  
[こちらのreleasesページ](https://github.com/takano536/multiple-renamer/releases)からダウンロードすることができます。

## 特徴
本ツールは、様々な正規表現を用いて、柔軟にファイル名を変更することができます。  
また、Windows Explorerのような[自然順ソート](https://ja.wikipedia.org/wiki/%E8%87%AA%E7%84%B6%E9%A0%86)が可能です。

## 使い方
「MultipleRenamer.exe」は、CLIソフトです。コマンドプロンプトを立ち上げ、以下のようなコマンドを打ち込み、使用してください。
```
MultipleRenamer.exe --help
```
以下のコマンドは、ファイル名を変換するコマンドの一例です。
```
MultipleRenamer.exe -i text.txt C:\Users\user\Music C:\Users\user\Documents -o "%foldername%_##.%ext%" -e .ini
```
以下は、実行結果例です。
```
C:\Users\user\Documents
text01.txt -> Documents_01.txt
text1.txt -> Documents_02.txt
text10.txt -> Documents_03.txt

C:\Users\user\Music
bar.mp3 -> Music_01.mp3
foo.mp3 -> Music_02.mp3

Proceed ([y]/n)? y

Rename was successful.
```
引数を何も指定せずに実行すると、利用可能なオプションが表示されます。
```
usage: MultipleRenamer.exe [-h] -i [INPUT [INPUT ...]] -o OUTPUT_NAME [-e [EXCLUDE [EXCLUDE ...]]] [-r REPLACE]
                           [-s START_NUMBER] [--used_char [{upper,lower,number} [{upper,lower,number} ...]]]
                           [--sort {folder,file,date,ext,file-desc,folder-desc,date-desc,ext-desc}] [--recursive]     
                           [--sequence]

optional arguments:
  -h, --help            show this help message and exit
  -i [INPUT [INPUT ...]], --input [INPUT [INPUT ...]]
                        input file or directory
  -o OUTPUT_NAME, --output_name OUTPUT_NAME
                        output filename pattern (example: "-o %filename% (#).%ext%")
                        #                   : number with zero padding
                        ?                   : random character
                        %#%                 : # (escape sequence)
                        %                   : % (escape sequence)
                        %filename-with-ext% : filename with extention
                        %filename%          : filename without extention
                        %ext%               : file extention
                        %foldername%        : parent foldername
                        %creation-date%     : creation date
                        %creation-time%     : creation time
                        %modified-date%     : modified date
                        %modified-time%     : modified time
                        %size%              : file size
  -e [EXCLUDE [EXCLUDE ...]], --exclude [EXCLUDE [EXCLUDE ...]]
                        exclude file, directory or extension
                        selecting an extension, prefix it with dot at the beginning
  -r REPLACE, --replace REPLACE
                        character replacement (example: "-r a:A")
  -s START_NUMBER, --start_number START_NUMBER
                        starting head number (default=1)
  --used_char [{upper,lower,number} [{upper,lower,number} ...]]
                        characters used in random characters
  --sort {folder,file,date,ext,file-desc,folder-desc,date-desc,ext-desc}
                        how to sort files (default=folder)
  --recursive           recursively get input files
  --sequence            sequential numbering across folders

error: the following arguments are required: -i/--input, -o/--output_name
```

## コマンドラインオプション
本ソフトでは、以下のオプションを指定できます。
#### 入力ファイル
```
-i <ファイルのパスやフォルダのパス>, --input <ファイルのパスやフォルダのパス>
必須の引数です。
ファイルのパスやフォルダのパスを複数指定することができます。
```
#### 出力ファイル名
```
-o <出力ファイル名>, --output_name <出力ファイル名>
必須の引数です。
出力ファイル名を指定します。
以下は、利用可能な正規表現です。
* #                   : 数字
* ?                   : ランダムな文字
* %#%                 : # (エスケープシーケンス)
* %%                  : % (エスケープシーケンス)
* %filename-with-ext% : 拡張子有りファイル名
* %filename%          : 拡張子なしファイル名
* %ext%               : ファイルの拡張子
* %foldername%        : 親フォルダ名
* %creation-date%     : 作成日
* %creation-time%     : 作成時間
* %modified-date%     : 更新日
* %modified-time%     : 更新時間
* %size%              : ファイルサイズ
```
#### 除外するファイル
```
-e <ファイルのパスやフォルダのパス>, --exclude <ファイルのパスやフォルダのパス>
ファイルのパスやフォルダのパス、拡張子を複数指定することができます。
拡張子を指定する場合は、先頭にドットを付けてください。
```
#### 置換
```
-r <元の文字列:置換する文字列>, --replace <元の文字列:置換する文字列>
特定の文字や文字列を置換することができます。
例えば、'aa'を'A'に置換したい場合は、"-r aa:A"と入力してください。
```
#### 開始番号
```
-s <開始番号>, --start_number <開始番号>
正規表現の数字の開始番号を指定します。
デフォルト値は「1」です。
```
#### ランダムな文字に使用する文字の種類
```
--used_char <upper|lower|number>
ランダムな文字に使用する文字の種類を指定します。
何も指定しなかった場合、upper、lower、numberのすべてが使用されます。
* upper  : 英大文字
* lower  : 英小文字
* number : 数字
```
#### ファイルの並び方
```
--sort <folder|file|date|ext|folder-desc|file-desc|date-desc|ext-desc>
ファイルの並び方を指定します。
デフォルト値は「folder」です。
* folder      : フォルダ名で昇順に並び、同一フォルダ内に複数のファイルが有る場合、ファイル名で昇順に並びます。
* file        : フォルダに関係なく、ファイル名で昇順に並びます。
* date        : 作成日時で昇順に並びます。Windowsのみで動作します。
* ext         : 拡張子で昇順に並び、同一拡張子ファイルが複数ある場合、ファイル名で昇順に並びます。
* folder-desc : フォルダ名で降順に並び、同一フォルダ内に複数のファイルが有る場合、ファイル名で降順に並びます。
* file-desc   : フォルダに関係なく、ファイル名で降順に並びます。
* date-desc   : 作成日時で降順に並びます。Windowsのみで動作します。
* ext-desc    : 拡張子で降順に並び、同一拡張子ファイルが複数ある場合、ファイル名で降順に並びます。
```
#### 入力ファイルを再帰的に取得する
```
--recursive
このオプションを指定すると、サブフォルダを含めた全てのファイルを取得します。
```
#### 異なるフォルダで連番を振る
```
--sequence
通常、フォルダが異なる場合、ナンバリングはリセットされます。
このオプションを指定すると、異なるフォルダであっても、ナンバリングがリセットされません。
```

## ライセンス
本ソフトは無保証です。詳しくは[LICENSE](LICENSE)をご覧ください。