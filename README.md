# Assistant.py

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

This script provides abstract Assistant API wapper with various utility functions.
For example, it can be used to get the folder structure of the local environment, check the content of files, and refactor them into the appropriate form.

このスクリプトは、さまざまなユーティリティ関数を備えた抽象的な Assistant API ラッパーを提供します。
例えば、生成AIがローカル環境のフォルダ構造を取得し、ファイルの内容を確認、適切な形へリファクタリングする用途があります。

## Description

This Python script includes the following utility functions:

この Python スクリプトには、次のユーティリティ関数が含まれています。

- `get_folder_structure`:

  Generate a string representing the folder structure recursively in a tree-like format. 

  フォルダ構造を再帰的に木構造の形式で表す文字列を生成します。


- `get_file_content`:

  Get the content of a file.

  ファイルの内容を取得します。

- `read_readme`:

  Check if the README.md file exists and return its content.

  README.md ファイルが存在するかどうかを確認し、その内容を返します。

- `run_command`:

  Execute a specified command and return its output.

  指定されたコマンドを実行し、その出力を返します。

- `write_content_to_file`:

  Write content to a specified file.

  コンテンツを指定されたファイルに書き込みます。

## Requirements

- Python 3.5 or later.

## How to use

To use this script, you need to do the following steps:

1. Install Python 3.5 or later.

2. Download the script.

3. Install the required packages. `pip install -r requirements.txt`

4. Set the `OPENAI_API_KEY` environment variable.

5. Run the script in command-line.

6. If you want to make AI remember the conversation, you need to run `assistant_remember_thread_id.zsh` or `assistant_remember_thread_id.bat`.

このスクリプトを使用するには、次の手順を実行する必要があります。

1. Python 3.5 以降をインストールします。

2. スクリプトをダウンロードします。

3. 必要なパッケージをインストールします。 `pip install -r requirements.txt`

4. 環境変数に `OPENAI_API_KEY` を設定します。

5. コマンドラインでスクリプトを実行します。

6. AI に会話を覚えさせたい場合は、`assistant_remember_thread_id.zsh` または `assistant_remember_thread_id.bat` を実行する必要があります。


### Examples

```
python assistant.py "get_folder_structure" --assistant_id="asst_sample"
```

or

```
python assistant.py "get_folder_structure" --assistant_name="Refactoring Developer"
```

If you want to make AI remember the conversation, you need to run the following command:
It depends on your operating system.

AI に会話を覚えさせたい場合は、次のコマンドを実行する必要があります。
これは、あなたのオペレーティングシステムによります。

Mac/Linux:
```
. assistant_remember_thread_id.zsh
```

Windows:
```
assistant_remember_thread_id.bat
```

When you refresh the terminal, you need to run the command again.

ターミナルをリフレッシュするときは、コマンドを再度実行する必要があります。

### Options

- `--assistant_name`:

  The name of the assistant. If not set, ASSISTANT_NAME environment variable is used.

  アシスタントの名前。設定されていない場合、ASSISTANT_NAME 環境変数が使用されます。


## Assistants

### Refactoring Developer

This GPT specializes in refactoring source code in software development. The main task is to analyze the source code and generate its refactored version. The refactored version is saved in the same directory as the original file with the suffix "_refactored".

このGPTは、ソフトウェア開発におけるソースコードのリファクタリングを専門としています。主な任務は、ソースコードを分析し、そのリファクタリング版を生成することです。リファクタリングされたバージョンは、オリジナルのファイルと同じディレクトリに「_refactored」の接尾辞を付けて保存されます。


#### Example

```
python assistant.py "refactor get_current_time.py" --assistant_name="Refactoring Developer"
```

Reads `get_current_time.py`

```python
import datetime
import pytz

def get_current_time(city):
    # タイムゾーンを設定
    if city == "Newyork":
        timezone = pytz.timezone("America/New_York")
    elif city == "London":
        timezone = pytz.timezone("Europe/London")
    elif city == "Tokyo":
        timezone = pytz.timezone("Asia/Tokyo")
    elif city == "Hanoi":
        timezone = pytz.timezone("Asia/Ho_Chi_Minh")
    elif city == "Mumbai":
        timezone = pytz.timezone("Asia/Kolkata")
    else:
        return "指定された都市はサポートされていません。"

    # 現在の日時を取得
    current_time = datetime.datetime.now(timezone)

    # ISO 8601形式で日時をフォーマット
    iso_time = current_time.isoformat()

    return iso_time

# 都市を指定して現在の日時を取得
city = "Tokyo"
current_time = get_current_time(city)
print(f"{city}の現在の日時は {current_time} です。")
```

Outputs `get_current_time_refactored.py`

```python
import datetime
import pytz

def get_timezone(city_name):
    # タイムゾーンを設定
    time_zones_dict = {
        'Newyork': pytz.timezone("America/New_York"),
        'London': pytz.timezone("Europe/London"),
        'Tokyo': pytz.timezone("Asia/Tokyo"),
        'Hanoi': pytz.timezone("Asia/Ho_Chi_Minh"),
        'Mumbai': pytz.timezone("Asia/Kolkata"),
    }
    return time_zones_dict.get(city_name)

def get_current_time(city_name):
    timezone = get_timezone(city_name)
    if not timezone:
        print("指定された都市はサポートされていません。")
        return

    # 現在の日時を取得
    current_time = datetime.datetime.now(timezone)

    # ISO 8601形式で日時をフォーマット
    iso_time = current_time.isoformat()
    return iso_time

def main():
    # 都市を指定して現在の日時を取得
    city = "Tokyo"
    current_time = get_current_time(city)

    if current_time:
        print(f"{city}の現在の日時は {current_time} です。")

if __name__ == "__main__":
    main()
```
