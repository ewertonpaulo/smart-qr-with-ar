import sys
import os
import time
from utils.utils import prompt, APP_NAME
from actions import (
    action_add_watermark_qr,
    action_add_memory_qr,
    action_create_ar_live_photo
)
from local_server import stop_local_server, start_local_server


def clear_screen():
    time.sleep(3)
    os.system('cls' if os.name == 'nt' else 'clear')

def print_menu():
    print("\n" + "=" * 50)
    print(f"{APP_NAME}")
    print("=" * 50)
    print("1) Add QR Code to an image")
    print("2) Add a memory to an image")
    print("3) Create 'Live Photo'")
    print("0) Exit")
    print("-" * 50)

def main():
    actions = {
        "1": action_add_watermark_qr,
        "2": action_add_memory_qr,
        "3": action_create_ar_live_photo
    }
    try:
        start_local_server()

        while True:
            print_menu()
            choice = prompt("Choose an option: ").strip()

            if choice == "0":
                break

            action = actions.get(choice)
            if action:
                action()
                # clear_screen()
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
