# assistant.py
import os
import sys
import argparse
import json
import subprocess
from time import sleep
from openai import OpenAI
from typing import Optional, Dict, Callable


def get_folder_structure(path='.', level=0, indent="    ", exclude_folders=None, max_items=30):
    """
    Generate a string representing the folder structure recursively in a tree-like format,
    skipping folders with a number of items exceeding max_items.
    
    :param path: The base directory path
    :param level: The current level in the tree
    :param indent: The indentation to use for levels
    :param exclude_folders: A list of folder names to exclude
    :param max_items: The maximum number of items allowed in a folder for it to be displayed.
                      Folders with more items than this number will not be displayed.
    :return: A string representing the folder structure
    """
    import os

    if exclude_folders is None:
        exclude_folders = ['__pycache__', '.git', '.vs', '.vscode', '.idea', 'venv', '.venv', 'env', 'node_modules', '.next', 'build', 'dist', 'output', 'bin']

    folder_structure_str = ""
    try:
        files_and_dirs = [f for f in os.listdir(path) if not any(excl in f for excl in exclude_folders)]
    except PermissionError:
        return folder_structure_str

    files_and_dirs.sort(key=lambda x: (os.path.isdir(os.path.join(path, x)), x.lower()))
    for i, name in enumerate(files_and_dirs, start=1):
        new_path = os.path.join(path, name)
        if os.path.isdir(new_path):
            items_in_dir = [f for f in os.listdir(new_path) if not any(excl in f for excl in exclude_folders)]
            # Check the number of items in the directory
            if max_items is None or (max_items is not None and len(items_in_dir) <= max_items):
                folder_structure_str += f"{indent * level}{'├── ' if i < len(files_and_dirs) else '└── '}{name}\n"
                folder_structure_str += get_folder_structure(new_path, level + 1, indent, exclude_folders, max_items)
        else:
            folder_structure_str += f"{indent * level}{'├── ' if i < len(files_and_dirs) else '└── '}{name}\n"

    return folder_structure_str

def get_file_content(file_paths):
    """
    Get the content of a file.
    
    :param file_paths: The paths to the file
    :return: The content of the file
    """
    if not isinstance(file_paths, list):
        with open(file_path, 'r') as file:
            return file.read()
    else:
        file_contents = {}
        for file_path in file_paths:
            with open(file_path, 'r', encoding="utf-8") as file:
                file_contents[file_path] = file.read()

        return json.dumps(file_contents)


def read_readme():
    # Check if the file exists
    if os.path.exists("README.md"):
        with open("README.md", "r", encoding="utf-8") as file:
            return file.read()
    else:
        return "The README.md file does not exist."


def run_command(command):
    """
    指定されたコマンドを実行し、その出力を返します。
    Args:
        command (str): 実行するコマンド。
    Returns:
        str: コマンドの実行結果。
    """
    try:
        # subprocess.runはPython3.5以上で利用可能
        # stdout=subprocess.PIPEはコマンドの標準出力をキャプチャするために必要
        # stderr=subprocess.STDOUTは標準エラー出力も標準出力にマージします
        # check=Trueはコマンドが非ゼロの終了コードで終了した場合に例外を発生させます
        # text=TrueはPython3.7以上で利用可能、出力を文字列として扱います（Python3.6以下ではuniversal_newlines=Trueを使用）
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=True, text=True, shell=True)
        return result.stdout
    except subprocess.CalledProcessError as e:
        return e.output


def write_content_to_file(file_path, content):
    try:
        # 現在の作業ディレクトリを取得
        current_directory = os.getcwd()
        print(f"Current working directory: {current_directory}")
        
        # ファイルパスからディレクトリのパスを取得
        directory = os.path.dirname(file_path)
        
        # ディレクトリが存在しない場合、再帰的にディレクトリを作成
        if not os.path.exists(directory) and directory != "":
            os.makedirs(directory)
        
        # ファイルにコンテンツを書き込み
        with open(file_path, 'w', encoding="utf-8") as file:
            file.write(content)
        
        return f"Content has been successfully written to {file_path}"
    except Exception as e:
        # エラー情報に現在の作業ディレクトリを含める
        return f"Error writing content to {file_path} in directory {current_directory}: {e}"


FunctionMap = Dict[str, Callable]
IAssistantChatResponse = Dict[str, any]


class Assistant:
    def __init__(self, assistant_id: str, functions: Optional[FunctionMap] = None, api_key: str = None):
        # Get the OpenAI API key from the environment variables
        # Japanese: 環境変数からOpenAI APIキーを取得
        if not api_key:
            # If the API key is not provided, try to get it from the environment variables
            # Japanese: APIキーが提供されていない場合は、環境変数から取得を試みる
            api_key = os.environ.get('OPENAI_API_KEY', None)

        self.openai = OpenAI(api_key=api_key)
        self.assistant_id = assistant_id
        self.functions = functions or {}

    def check_run_status(self, thread_id: str, run_id: str):
        run = self.openai.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )
        
        if run.status in ["queued", "in_progress", "cancelling"]:
            sleep(1)
            return self.check_run_status(thread_id, run_id)
        
        return run

    def handle_requires_action(self, thread_id: str, run_id: str, verbose: bool = False):
        run = self.openai.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run_id
        )

        if run.status == "requires_action":
            if run.required_action.type == 'submit_tool_outputs':
                tool_calls = run.required_action.submit_tool_outputs.tool_calls

                for tool_call in tool_calls:
                    if tool_call.type == 'function':
                        function_name = tool_call.function.name

                        if self.functions:
                            if function_name in self.functions:
                                args = tool_call.function.arguments

                                parsed_args = {}
                                if not args == "":
                                    parsed_args = json.loads(args)

                                if verbose:
                                    print(f"\nCalling function \"{function_name}\" with args:\n {json.dumps(parsed_args, indent=2)}")

                                result = self.functions[function_name](**parsed_args)

                                if verbose:
                                    print("\nFunction Result\n", result)

                                self.openai.beta.threads.runs.submit_tool_outputs(
                                    thread_id=thread_id,
                                    run_id=run.id,
                                    tool_outputs=[
                                        {
                                            'tool_call_id': tool_call.id,
                                            'output': result
                                        }
                                    ]
                                )
                            else:
                                # Throw an error
                                raise Exception(f"Function {function_name} not found in functions map")


    def chat(self, user_message: str, thread_id: Optional[str] = None, verbose: bool = False) -> IAssistantChatResponse:
        if verbose:
            if user_message:
                print("\nUser Message\n", user_message)
            else:
                print("userMessage is empty")


        new_message = {
            "role": "user",
            "content": user_message
        }

        if not thread_id:
            thread = self.openai.beta.threads.create()
            thread_id = thread.id

        message = self.openai.beta.threads.messages.create(
            thread_id,
            role="user",
            content=user_message
        )

        run = self.openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id,
        )

        run = self.check_run_status(thread_id, run.id)

        if verbose:
            print("\nRun Status: ", run.status)

        if run.status == "failed":
            run = self.openai.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )

            raise Exception(run.last_error.code, run.last_error.message)
        
        while run.status == "requires_action":
            self.handle_requires_action(thread_id, run.id, verbose=verbose)

            run = self.check_run_status(thread_id, run.id)

        messages = self.openai.beta.threads.messages.list(thread_id)

        generate_env_var_regist_shell_script(thread_id)
        generate_env_var_register_batch_script(thread_id)

        if verbose:
            print("\nThread ID\n", thread_id)

        print("\nAssistant Messages\n", messages.data[0].content[0].text.value)

        return {
            "thread_id": thread_id,
            "messages": messages
        }

def generate_env_var_regist_shell_script(env_var_value):
    env_var_name = "THREAD_ID"
    script_content = f"#!/bin/zsh\nexport {env_var_name}={env_var_value}\n"

    # シェルスクリプトファイルを書き出し、既に存在する場合は上書きする
    script_filename = "assistant_remember_thread_id.zsh"
    with open(script_filename, "w") as script_file:
        script_file.write(script_content)

def generate_env_var_register_batch_script(env_var_value):
    env_var_name = "THREAD_ID"
    # Windowsのバッチファイル用に環境変数を設定するコマンドを作成
    script_content = f"@echo off\nset {env_var_name}={env_var_value}\n"

    # バッチスクリプトファイル名
    script_filename = "assistant_remember_thread_id.bat"
    
    # バッチスクリプトファイルを書き出し、既に存在する場合は上書きする
    with open(script_filename, "w") as script_file:
        script_file.write(script_content)

def get_or_create(assistant_name):
    if not assistant_name:
        raise ValueError("Assistant name is required")

    assistant_name = assistant_name.replace(" ", "_").lower()
    client = OpenAI()
    # ファイルを開く
    with open(f"./assistants/{assistant_name}.json", 'r') as f:
        # ファイルが見つからない場合はエラーをスロー
        if not f:
            raise FileNotFoundError("File not found")

        data = json.load(f)
        name_of_assistant = data['name'] + " Version:" + str(data['version'])
        model = data['model']
        name = name_of_assistant
        description = data['description']
        instructions = data['instructions']
        tools = data['tools']
        file_ids = data['file_ids']
        metadata = data['metadata']

        my_assistants = client.beta.assistants.list(
            order="desc",
            limit="20",
        )

        for assistant in my_assistants.data:
            if assistant.name == name_of_assistant:
                assistant_id = assistant.id

                client.beta.assistants.update(
                    assistant_id,
                    model=model,
                    name=name_of_assistant,
                    description=description,
                    instructions=instructions,
                    tools=tools,
                    file_ids=file_ids,
                    metadata=metadata,
                )
                return assistant.id

        # アシスタントが見つからない場合はアシスタントを作成
        assistant = client.beta.assistants.create(
            model=model,
            name=name_of_assistant,
            description=description,
            instructions=instructions,
            tools=tools,
            file_ids=file_ids,
            metadata=metadata,
        )

        return assistant.id

def main():
    thread_id = os.environ.get('THREAD_ID', None)

    # argparseを使ってコマンドライン引数を処理する
    parser = argparse.ArgumentParser(description="Process some parameters.")
    parser.add_argument('user_message', nargs='*', help='User message to process')
    parser.add_argument('--assistant_name', help='Name of the assistant')
    parser.add_argument('--assistant_id', help='Name of the assistant')
    args = parser.parse_args()

    assistant_id = args.assistant_id

    # assistant_idが指定されていない場合は、assistant_nameを使用してアシスタントを取得または作成する
    if not assistant_id:
        # コマンドライン引数または環境変数からassistant_nameを取得する
        assistant_name = args.assistant_name or os.environ.get('ASSISTANT_NAME')
        if not assistant_name:
            print("Error: assistant_name is not specified via command line or environment variable.")
            sys.exit(1)

        assistant_id = get_or_create(assistant_name)

    user_message = " ".join(args.user_message)

    assistant = Assistant(
        assistant_id=assistant_id,
        functions={
            "get_file_content": get_file_content,
            "get_folder_structure": get_folder_structure,
            "read_readme": read_readme,
            "run_command": run_command,
            "write_content_to_file": write_content_to_file
        }
    )

    response = assistant.chat(user_message, thread_id, verbose=True)


if __name__ == "__main__":
    main()
