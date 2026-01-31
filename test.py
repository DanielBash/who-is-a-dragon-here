import os
import sys
import ast


def obfuscate_python_file(filepath):
    """Convert a Python file to a one-liner with exec and LINESPLITTER"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Check if the file is already obfuscated
        if 'exec(' in content and 'LINESPLITTER' in content:
            print(f"Skipping already obfuscated file: {filepath}")
            return

        # Validate the code is valid Python syntax first
        try:
            ast.parse(content)
        except SyntaxError as e:
            print(f"Syntax error in {filepath}: {e}")
            return

        # Replace \n with LINESPLITTER, then escape quotes
        linesplit_content = content.replace('\n', 'LINESPLITTER')
        # Escape backslashes and quotes for the string literal
        escaped_content = linesplit_content.replace('\\', '\\\\').replace("'", "\\'")

        # Create the one-liner
        one_liner = f"exec('''{escaped_content}'''.replace('LINESPLITTER', '\\n'))"

        # Write back to the file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(one_liner)

        print(f"Obfuscated: {filepath}")

    except Exception as e:
        print(f"Error processing {filepath}: {e}")


def process_directory(directory='.'):
    """Recursively process all Python files in directory"""
    for root, dirs, files in os.walk(directory):
        # Skip __pycache__ directories
        dirs[:] = [d for d in dirs if d != '__pycache__']

        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                # Skip this script itself
                if os.path.abspath(filepath) == os.path.abspath(__file__):
                    print(f"Skipping self: {filepath}")
                    continue

                obfuscate_python_file(filepath)


def decode_obfuscated_file(filepath):
    """Decode a file that was obfuscated with this script"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract the string from exec()
        if content.startswith("exec('''") and "'''.replace('LINESPLITTER', '\\n'))" in content:
            # Remove the exec wrapper
            inner = content[7:]  # Remove "exec('''"
            inner = inner[:-34]  # Remove "'''.replace('LINESPLITTER', '\\n'))"

            # Unescape
            decoded = inner.replace('\\\\', '\\').replace("\\'", "'")

            # Replace LINESPLITTER back to newlines
            original = decoded.replace('LINESPLITTER', '\n')

            return original
        return None
    except Exception as e:
        print(f"Error decoding {filepath}: {e}")
        return None


def main():
    print("Python File Obfuscator")
    print("======================")
    print("1. Obfuscate all Python files in current directory and subdirectories")
    print("2. Decode a specific obfuscated file")
    print("3. Exit")

    choice = input("\nSelect option (1-3): ").strip()

    if choice == '1':
        confirm = input(
            "WARNING: This will overwrite all Python files in this directory and subdirectories. Continue? (y/N): ")
        if confirm.lower() == 'y':
            current_dir = os.path.dirname(os.path.abspath(__file__))
            print(f"Processing directory: {current_dir}")
            process_directory(current_dir)
            print("\nObfuscation complete!")
        else:
            print("Cancelled.")

    elif choice == '2':
        filepath = input("Enter path to obfuscated file: ").strip()
        if os.path.exists(filepath):
            decoded = decode_obfuscated_file(filepath)
            if decoded:
                print("\nDecoded content:")
                print("-" * 40)
                print(decoded)
                print("-" * 40)

                save = input("\nSave decoded content to file? (y/N): ").lower()
                if save == 'y':
                    new_path = filepath + '.decoded.py'
                    with open(new_path, 'w', encoding='utf-8') as f:
                        f.write(decoded)
                    print(f"Saved to: {new_path}")
            else:
                print("File doesn't appear to be obfuscated with this method.")
        else:
            print("File not found.")

    elif choice == '3':
        print("Exiting.")
        sys.exit(0)

    else:
        print("Invalid choice.")


if __name__ == "__main__":
    main()