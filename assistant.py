# assistant.py
import os
import sys
import json
import subprocess
from time import sleep
from openai import OpenAI
from typing import Optional, Dict, Callable


def get_folder_structure(path='.', level=0, indent="    ", exclude_folders=None):
    """
    Generate a string representing the folder structure recursively in a tree-like format.
    
    :param path: The base directory path
    :param level: The current level in the tree
    :param indent: The indentation to use for levels
    :param exclude_folders: A list of folder names to exclude
    :return: A string representing the folder structure
    """
    import os

    if exclude_folders is None:
        exclude_folders = ['__pycache__', '.git', '.vscode', '.idea', 'venv', 'env', 'node_modules', '.next']

    folder_structure_str = ""
    try:
        files_and_dirs = [f for f in os.listdir(path) if not any(excl in f for excl in exclude_folders)]
    except PermissionError:  # In case of permission errors, just return an empty string
        return folder_structure_str

    files_and_dirs.sort(key=lambda x: (os.path.isdir(os.path.join(path, x)), x.lower()))
    for i, name in enumerate(files_and_dirs, start=1):
        if os.path.isdir(os.path.join(path, name)):
            folder_structure_str += f"{indent * level}{'├── ' if i < len(files_and_dirs) else '└── '}{name}\n"
            new_path = os.path.join(path, name)
            folder_structure_str += get_folder_structure(new_path, level + 1, indent, exclude_folders)
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
            with open(file_path, 'r') as file:
                file_contents[file_path] = file.read()

        return json.dumps(file_contents)


def read_readme():
    # Check if the file exists
    if os.path.exists("README.md"):
        with open("README.md", "r") as file:
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
        with open(file_path, 'w') as file:
            file.write(content)
        
        return f"Content has been successfully written to {file_path}"
    except Exception as e:
        # エラー情報に現在の作業ディレクトリを含める
        return f"Error writing content to {file_path} in directory {current_directory}: {e}"


FunctionMap = Dict[str, Callable]
IAssistantChatResponse = Dict[str, any]


class Assistant:
    def __init__(self, assistant_id: str, functions: Optional[FunctionMap] = None, api_key: str = None):
        if not api_key:
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


    def chat(self, initial_message: str, thread_id: Optional[str] = None, verbose: bool = False) -> IAssistantChatResponse:
        if verbose:
            if initial_message:
                print("\nUser Message\n", initial_message)
            else:
                print("userMessage is empty")


        new_message = {
            "role": "user",
            "content": initial_message
        }

        if not thread_id:
            thread = self.openai.beta.threads.create()
            thread_id = thread.id

        message = self.openai.beta.threads.messages.create(
            thread_id,
            role="user",
            content=initial_message
        )

        run = self.openai.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id,
        )

        run = self.check_run_status(thread_id, run.id)

        if verbose:
            print("\nRun Status: ", run.status)
        
        while run.status == "requires_action":
            self.handle_requires_action(thread_id, run.id, verbose=verbose)

            run = self.check_run_status(thread_id, run.id)

        messages = self.openai.beta.threads.messages.list(thread_id)

        generate_env_var_regist_shell_script(thread_id)

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

def main():
    thread_id = os.environ.get('THREAD_ID', None)

    initial_message = "Freely look into this project and give your advice in Japanese."

    if len(sys.argv) > 1:
        initial_message = " ".join(sys.argv[1:])

    devai_assistant = Assistant(
        assistant_id="asst_sV83OHx15YOcOuCW27Al4m4J",
        functions={
            "get_file_content": get_file_content,
            "get_folder_structure": get_folder_structure,
            "read_readme": read_readme,
            "run_command": run_command,
            "write_content_to_file": write_content_to_file
        }
    )

    response = devai_assistant.chat(initial_message, thread_id, verbose=True)


if __name__ == "__main__":
    main()
