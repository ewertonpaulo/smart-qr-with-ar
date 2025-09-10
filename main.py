import sys
import os
from utils.utils import prompt, APP_NAME
from actions import (
    action_add_watermark_qr,
    action_watermark_with_media_link
)
from local_server import stop_local_server, start_local_server


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    print("\n" + "=" * 50)
    print(f"{APP_NAME}")
    print("=" * 50)
    print("1) Add a memory to image")
    print("2) Add QR Code to an image")
    print("0) Exit")
    print("-" * 50)

def main():
    actions = {
        "2": action_add_watermark_qr,
        "1": action_watermark_with_media_link,
    }
    try:
        start_local_server()

        while True:
            clear_screen()
            print_menu()
            choice = prompt("Choose an option: ").strip()

            if choice == "0":
                break

            action = actions.get(choice)
            if action:
                action()
            else:
                print("Invalid option. Please try again.")
    finally:
        print("Shutting down local server (if active)...")
        stop_local_server()
        print("Program finished.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)