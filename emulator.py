import argparse
import os
import getpass
import socket


class VFSApp:
    def __init__(self, vfs_path='./vfs_root', script_path=None):
        self.vfs_path = vfs_path
        self.script_path = script_path
        self.current_vfs = {}
        self.current_dir = "/"
        self.initialize_vfs()
        self.print_output(f"VFS Emulator started")
        self.print_output(f"VFS path: {vfs_path}")

        if script_path:
            self.print_output(f"Script to execute: {script_path}")
            self.run_script()
            self.print_output("\n=== Script executed, switching to interactive mode ===")

        self.run_interactive()

    def print_output(self, text):
        print(text)

    def execute_command(self, command_line):
        command_line = command_line.strip()
        if not command_line:
            return True

        try:
            tokens = self.parse_command(command_line)
            if tokens:
                command = tokens[0]
                args = tokens[1:] if len(tokens) > 1 else []

                if command == "exit":
                    return False
                elif command == "ls":
                    self.list_directory(args)
                elif command == "cd":
                    self.change_directory(args)
                else:
                    self.print_output(f"Unknown command: {command}")

        except ValueError as e:
            self.print_output(f"Syntax error: {e}")
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
            return

        self.print_output(f"# Executing script: {self.script_path}")

        try:
            with open(self.script_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    self.print_output(f"[Script:{line_num}] > {line}")
                    self.execute_command(line)

        except Exception as e:
            self.print_output(f"Script reading error: {e}")

    def initialize_vfs(self):
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
                                    "documents": {"type": "directory", "content": {}, "perms": "755"},
                                    "photos": {"type": "directory", "content": {}, "perms": "755"}
                                },
                                "perms": "755"
                            }
                        },
                        "perms": "755"
                    },
                    "etc": {
                        "type": "directory",
                        "content": {
                            "config.txt": {"type": "file", "size": 1024, "perms": "644"},
                            "settings.ini": {"type": "file", "size": 512, "perms": "644"}
                        },
                        "perms": "755"
                    },
                    "readme.txt": {"type": "file", "size": 2048, "perms": "644"}
                },
                "perms": "755"
            }
        }
        self.current_dir = "/"

        if os.path.exists(self.vfs_path):
            import shutil
            shutil.rmtree(self.vfs_path)
        os.makedirs(self.vfs_path, exist_ok=True)

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
                return

            items = []
            for name, item in target_dir["content"].items():
                if show_details:
                    item_type = "d" if item["type"] == "directory" else "f"
                    perms = item.get("perms", "???")
                    size = f" {item['size']}b" if item["type"] == "file" else ""
                    items.append(f"{item_type}{perms} {name}{size}")
                else:
                    items.append(name)

            # Output all items in one line separated by spaces
            if items:
                self.print_output(" ".join(items))
            else:
                self.print_output("")  # Empty line for empty directory

        except Exception as e:
            self.print_output(f"ls error: {e}")

    def change_directory(self, args):
        if not args:
            self.print_output("Error: specify path")
            return

        path = args[0]
        try:
            if path == "/":
                self.current_dir = "/"
            elif path == "..":
                if self.current_dir == "/":
                    self.print_output("Error: already in root directory")
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
                elif target["type"] != "directory":
                    self.print_output(f"Error: {new_path} is not a directory")
                else:
                    self.current_dir = new_path
            self.print_output(f"Current directory: {self.current_dir}")
        except Exception as e:
            self.print_output(f"cd error: {e}")

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

    def path_exists(self, path):
        if path == "/":
            return True

        parts = path.strip('/').split('/')
        current = self.current_vfs.get("/")
        for part in parts:
            if part and current and current["type"] == "directory":
                current = current["content"].get(part)
            else:
                return False
        return current is not None

    def reverse_text(self, args):
        if not args:
            self.print_output("Error: specify text to reverse")
            return

        text = " ".join(args)
        reversed_text = text[::-1]
        self.print_output(f"Reversed: {reversed_text}")

    def find_in_vfs(self, args):
        if not args:
            self.print_output("Error: specify name to search")
            return

        search_name = args[0]
        results = []
        self._search_recursive("/", self.current_vfs["/"], search_name, results)

        if results:
            self.print_output(f"Found {len(results)} results:")
            for result in results:
                self.print_output(f"  {result}")
        else:
            self.print_output("No results found")

    def _search_recursive(self, current_path, current_item, search_name, results):
        if current_item["type"] == "directory":
            for name, item in current_item["content"].items():
                item_path = f"{current_path}/{name}" if current_path != "/" else f"/{name}"
                if name == search_name:
                    item_type = "directory" if item["type"] == "directory" else "file"
                    results.append(f"{item_path} ({item_type})")
                self._search_recursive(item_path, item, search_name, results)

    def change_permissions(self, args):
        if len(args) < 2:
            self.print_output("Error: specify permissions and path")
            return
        perms = args[0]
        target_path = args[1]
        if not perms.isdigit() or len(perms) != 3 or not all(0 <= int(p) <= 7 for p in perms):
            self.print_output("Error: permissions must be a three-digit number")
            return
        if not target_path.startswith('/'):
            target_path = os.path.join(self.current_dir, target_path).replace('\\', '/')
        try:
            target_item = self.get_directory_by_path(target_path)
            if not target_item:
                self.print_output(f"Error: {target_path} does not exist")
                return
            target_item["perms"] = perms
            self.print_output(f"Permissions for {target_path} changed to {perms}")

        except Exception as e:
            self.print_output(f"chmod error: {e}")

    def run_interactive(self):
        # Get real OS data
        username = getpass.getuser()
        hostname = socket.gethostname()

        self.print_output("\nInteractive mode. Type 'exit' to quit")

        while True:
            try:
                # Create prompt based on real OS data
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
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    print("=" * 50)
    print("Emulator startup parameters:")
    print(f"VFS path: {args.vfs_path}")
    print(f"Script: {args.script if args.script else 'Not specified'}")
    print("=" * 50)

    app = VFSApp(vfs_path=args.vfs_path, script_path=args.script)