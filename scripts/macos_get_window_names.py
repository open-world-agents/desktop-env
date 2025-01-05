import subprocess


def get_all_window_info():
    script = """
    tell application "System Events"
        set windowList to {}
        repeat with proc in (every application process whose background only is false)
            set procName to name of proc
            repeat with w in (every window of proc)
                try
                    set windowName to name of w
                    copy {procName, windowName} to end of windowList
                end try
            end repeat
        end repeat
        return windowList
    end tell
    """

    try:
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            # Parse AppleScript result into a list
            output = result.stdout.strip()
            # Process only if output is not empty
            if output:
                # Split items by comma
                items = output.split(", ")
                windows = []
                # Pair app names with window names
                for i in range(0, len(items), 2):
                    if i + 1 < len(items):
                        app_name = items[i].strip("{}")
                        window_name = items[i + 1].strip("{}")
                        windows.append((app_name, window_name))
                return windows
            return []
        else:
            print(f"Error: {result.stderr}")
            return []
    except Exception as e:
        print(f"Error: {e}")
        return []


def print_window_info():
    windows = get_all_window_info()
    if windows:
        print("\nCurrently Open Windows:")
        print("-" * 50)
        for i, (app_name, window_name) in enumerate(windows, 1):
            print(f"{i}. App: {app_name}")
            print(f"   Window: {window_name}")
            print("-" * 50)
    else:
        print("No windows found.")


# Execute
if __name__ == "__main__":
    print_window_info()
