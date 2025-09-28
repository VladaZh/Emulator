import argparse
import os
import getpass
import socket
import csv
import base64
import sys
from datetime import datetime


class VFSApp:
    def __init__(self, vfs_path='./vfs_root', script_path=None, vfs_csv=None):
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.vfs_csv = vfs_csv
        self.current_vfs = {}
        self.current_dir = "/"

        # Загружаем VFS из CSV или создаем стандартную
        if not self.load_vfs_from_csv():
            self.initialize_default_vfs()

        self.print_output(f"VFS Emulator started")
        self.print_output(f"VFS path: {vfs_path}")
        if vfs_csv:
            self.print_output(f"VFS source: {vfs_csv}")

        if script_path:
            self.print_output(f"Script to execute: {script_path}")
            script_completed = self.run_script()

            if script_completed:
                self.print_output("Script completed successfully")
                sys.exit(0)  # Завершаем программу после успешного скрипта
            else:
                self.print_output("Script execution failed")
                sys.exit(1)  # Завершаем программу с ошибкой после неудачного скрипта

        # Только если скрипт не указан, переходим в интерактивный режим
        self.run_interactive()

    def load_vfs_from_csv(self):
        """Загрузка VFS из CSV файла"""
        if not self.vfs_csv:
            return False

        if not os.path.exists(self.vfs_csv):
            self.print_output(f"Error: VFS CSV file '{self.vfs_csv}' not found")
            return False

        try:
            self.current_vfs = {"/": {"type": "directory", "content": {}, "perms": "755"}}

            with open(self.vfs_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)

                for row_num, row in enumerate(reader, 1):
                    if not self.validate_csv_row(row, row_num):
                        continue

                    path = row['path'].strip()
                    item_type = row['type'].strip()
                    perms = row.get('perms', '644').strip()

                    # Создаем структуру директорий
                    self.create_path_structure(path, item_type, perms, row, row_num)

            self.print_output(f"VFS loaded successfully from {self.vfs_csv}")
            return True

        except Exception as e:
            self.print_output(f"Error loading VFS from CSV: {e}")
            return False

    def validate_csv_row(self, row, row_num):
        """Валидация строки CSV"""
        required_fields = ['path', 'type']
        for field in required_fields:
            if field not in row or not row[field]:
                self.print_output(f"Error in row {row_num}: missing required field '{field}'")
                return False

        if row['type'] not in ['file', 'directory']:
            self.print_output(f"Error in row {row_num}: type must be 'file' or 'directory'")
            return False

        return True

    def create_path_structure(self, path, item_type, perms, row, row_num):
        """Создание структуры пути в VFS"""
        if path == "/":
            return

        parts = path.strip('/').split('/')
        current = self.current_vfs["/"]

        # Создаем промежуточные директории
        for part in parts[:-1]:
            if part not in current['content']:
                current['content'][part] = {
                    "type": "directory",
                    "content": {},
                    "perms": "755"
                }
            current = current['content'][part]
            if current['type'] != 'directory':
                self.print_output(f"Error in row {row_num}: '{part}' is not a directory")
                return

        # Создаем конечный элемент
        filename = parts[-1]
        if item_type == 'directory':
            current['content'][filename] = {
                "type": "directory",
                "content": {},
                "perms": perms
            }
        else:  # file
            size = int(row.get('size', 0))
            content_b64 = row.get('content', '')
            content = base64.b64decode(content_b64).decode('utf-8') if content_b64 else ""

            current['content'][filename] = {
                "type": "file",
                "size": size,
                "content": content,
                "perms": perms
            }

    def initialize_default_vfs(self):
        """Создание VFS по умолчанию"""
        self.current_vfs = {
            "/": {
                "type": "directory",
                "content": {
                    "home": {
                        "type": "directory",
                        "content": {
                            "user": {
                                "type": "directory",
                                "content": {
                                    "documents": {
                                        "type": "directory",
                                        "content": {
                                            "readme.txt": {
                                                "type": "file",
                                                "size": 1024,
                                                "content": "Welcome to VFS\nLine 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7\nLine 8\nLine 9\nLine 10",
                                                "perms": "644"
                                            },
                                            "notes.txt": {
                                                "type": "file",
                                                "size": 512,
                                                "content": "Important notes:\nNote 1\nNote 2\nNote 3\nNote 4\nNote 5",
                                                "perms": "644"
                                            }
                                        },
                                        "perms": "755"
                                    },
                                    "photos": {
                                        "type": "directory",
                                        "content": {},
                                        "perms": "755"
                                    }
                                },
                                "perms": "755"
                            }
                        },
                        "perms": "755"
                    },
                    "etc": {
                        "type": "directory",
                        "content": {
                            "config.txt": {
                                "type": "file",
                                "size": 512,
                                "content": "key=value\nserver=localhost\nport=8080\ntimeout=30",
                                "perms": "644"
                            }
                        },
                        "perms": "755"
                    },
                    "readme.txt": {
                        "type": "file",
                        "size": 2048,
                        "content": "VFS Emulator\nThis is a virtual file system\nYou can use commands like ls, cd, head, date",
                        "perms": "644"
                    }
                },
                "perms": "755"
            }
        }

    def print_output(self, text):
        print(text)

    def execute_command(self, command_line):
        command_line = command_line.strip()
        if not command_line:
            return True

        try:
            tokens = self.parse_command(command_line)
            if not tokens:
                return True

            command = tokens[0]
            args = tokens[1:] if len(tokens) > 1 else []

            if command == "exit":
                return False
            elif command == "ls":
                return self.list_directory(args)
            elif command == "cd":
                return self.change_directory(args)
            elif command == "head":
                return self.head_file(args)
            elif command == "date":
                return self.show_date(args)
            else:
                self.print_output(f"Unknown command: {command}")
                return True  # Продолжаем выполнение даже при неизвестной команде

        except ValueError as e:
            self.print_output(f"Syntax error: {e}")
            return True
        except Exception as e:
            self.print_output(f"Command execution error: {e}")
            return True

    def parse_command(self, command_line):
        tokens = []
        current_token = ""
        in_quotes = False
        quote_char = None

        for char in command_line:
            if char in ['"', "'"]:
                if not in_quotes:
                    in_quotes = True
                    quote_char = char
                elif char == quote_char:
                    in_quotes = False
                    quote_char = None
                else:
                    current_token += char
            elif char == ' ' and not in_quotes:
                if current_token:
                    tokens.append(current_token)
                    current_token = ""
            else:
                current_token += char

        if current_token:
            tokens.append(current_token)

        if in_quotes:
            raise ValueError("Unclosed quotes in command")

        return tokens

    def run_script(self):
        if not self.script_path or not os.path.exists(self.script_path):
            self.print_output(f"Error: Script {self.script_path} not found")
            return False

        self.print_output(f"# Executing script: {self.script_path}")

        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    self.print_output(f"[Script:{line_num}] > {line}")

                    success = self.execute_command(line)
                    if not success and line == "exit":
                        return True  # exit - нормальное завершение
                    elif not success:
                        self.print_output(f"Script stopped at line {line_num} due to error")
                        return False

            return True

        except Exception as e:
            self.print_output(f"Script reading error: {e}")
            return False

    def list_directory(self, args):
        try:
            show_details = "-l" in args
            path_args = [arg for arg in args if arg != "-l"]

            if not path_args:
                target_path = self.current_dir
            else:
                target_path = path_args[0]
                if not target_path.startswith('/'):
                    target_path = os.path.join(self.current_dir, target_path).replace('\\', '/')

            target_dir = self.get_directory_by_path(target_path)
            if not target_dir or target_dir["type"] != "directory":
                self.print_output(f"Error: {target_path} is not a directory")
                return False

            items = []
            for name, item in target_dir["content"].items():
                if show_details:
                    item_type = "d" if item["type"] == "directory" else "-"
                    perms = item.get("perms", "???")
                    if item["type"] == "file":
                        size = f" {item['size']}b"
                        items.append(f"{item_type}{perms} {name}{size}")
                    else:
                        items.append(f"{item_type}{perms} {name}")
                else:
                    items.append(name)

            if items:
                self.print_output(" ".join(items))
            else:
                self.print_output("")

            return True

        except Exception as e:
            self.print_output(f"ls error: {e}")
            return False

    def change_directory(self, args):
        if not args:
            self.print_output("Error: specify path")
            return False

        path = args[0]
        try:
            if path == "/":
                self.current_dir = "/"
            elif path == "..":
                if self.current_dir == "/":
                    self.print_output("Error: already in root directory")
                    return False
                else:
                    parts = self.current_dir.rstrip('/').split('/')
                    self.current_dir = '/' + '/'.join(parts[:-1]) if len(parts) > 1 else "/"
            else:
                if path.startswith('/'):
                    new_path = path
                else:
                    new_path = os.path.join(self.current_dir, path).replace('\\', '/')
                target = self.get_directory_by_path(new_path)
                if not target:
                    self.print_output(f"Error: path {new_path} does not exist")
                    return False
                elif target["type"] != "directory":
                    self.print_output(f"Error: {new_path} is not a directory")
                    return False
                else:
                    self.current_dir = new_path
            return True

        except Exception as e:
            self.print_output(f"cd error: {e}")
            return False

    def head_file(self, args):
        """Реализация команды head - вывод первых строк файла"""
        try:
            # Парсим аргументы
            lines_to_show = 10  # значение по умолчанию
            file_path = None

            i = 0
            while i < len(args):
                if args[i] == "-n" and i + 1 < len(args):
                    try:
                        lines_to_show = int(args[i + 1])
                        i += 2
                    except ValueError:
                        self.print_output(f"Error: invalid number of lines: {args[i + 1]}")
                        return False
                elif not args[i].startswith("-"):
                    file_path = args[i]
                    i += 1
                else:
                    self.print_output(f"Error: unknown option: {args[i]}")
                    return False

            if not file_path:
                self.print_output("Error: specify file path")
                return False

            # Получаем полный путь к файлу
            if not file_path.startswith('/'):
                file_path = os.path.join(self.current_dir, file_path).replace('\\', '/')

            # Находим файл в VFS
            file_item = self.get_directory_by_path(file_path)
            if not file_item:
                self.print_output(f"Error: file {file_path} not found")
                return False
            elif file_item["type"] != "file":
                self.print_output(f"Error: {file_path} is not a file")
                return False

            # Получаем содержимое файла и выводим первые строки
            content = file_item.get("content", "")
            lines = content.split('\n')

            for i in range(min(lines_to_show, len(lines))):
                self.print_output(lines[i])

            return True

        except Exception as e:
            self.print_output(f"head error: {e}")
            return False

    def show_date(self, args):
        """Реализация команды date - вывод текущей даты и времени"""
        try:
            # Простая реализация без поддержки форматов
            current_time = datetime.now()
            formatted_time = current_time.strftime("%a %b %d %H:%M:%S %Z %Y")
            self.print_output(formatted_time)
            return True
        except Exception as e:
            self.print_output(f"date error: {e}")
            return False

    def get_directory_by_path(self, path):
        if path == "/":
            return self.current_vfs.get("/")

        parts = path.strip('/').split('/')
        current = self.current_vfs.get("/")

        for part in parts:
            if not part or not current or current["type"] != "directory":
                return None
            current = current["content"].get(part)

        return current

    def run_interactive(self):
        username = getpass.getuser()
        hostname = socket.gethostname()

        self.print_output("\nInteractive mode. Type 'exit' to quit")

        while True:
            try:
                prompt = f"{username}@{hostname}:{self.current_dir}$ "
                command = input(prompt).strip()
                if not self.execute_command(command):
                    break
            except KeyboardInterrupt:
                self.print_output("\nShutting down...")
                break
            except EOFError:
                self.print_output("\nShutting down...")
                break


def parse_arguments():
    parser = argparse.ArgumentParser(description='VFS Emulator')
    parser.add_argument('--vfs-path', '-v', type=str, default='./vfs_root',
                        help='Path to VFS physical location')
    parser.add_argument('--script', '-s', type=str,
                        help='Path to startup script')
    parser.add_argument('--vfs-csv', '-c', type=str,
                        help='Path to VFS CSV source file')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    print("=" * 50)
    print("Emulator startup parameters:")
    print(f"VFS path: {args.vfs_path}")
    print(f"Script: {args.script if args.script else 'Not specified'}")
    print(f"VFS CSV: {args.vfs_csv if args.vfs_csv else 'Default VFS'}")
    print("=" * 50)

    app = VFSApp(vfs_path=args.vfs_path, script_path=args.script, vfs_csv=args.vfs_csv)