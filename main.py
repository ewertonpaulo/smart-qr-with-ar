import sys
import os
from utils.utils import prompt, APP_NAME
from actions import (
    action_generate_qr,
    action_add_watermark_qr,
    action_media_qr_local
)
from local_server import stop_local_server

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    print("\n" + "=" * 50)
    print(f"{APP_NAME}")
    print("=" * 50)
    print("1) Generate QR Code (standard or artistic)")
    print("2) Publish media and generate QR with local link")
    print("3) Add QR Code (standard or artistic) to an image")
    print("0) Exit")
    print("-" * 50)

def main():
    actions = {
        "1": action_generate_qr,
        "2": action_media_qr_local,
        "3": action_add_watermark_qr,
    }
    try:
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