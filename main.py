# main.py

import sys
from utils.utils import prompt, APP_NAME
from actions import (
    action_generate_qr,
    action_add_watermark_qr,
    action_media_qr_local
)
from local_server import stop_local_server

def print_menu():
    print("\n" + "=" * 50)
    print(f"{APP_NAME}")
    print("=" * 50)
    print("1) Gerar QR Code (padrão ou artístico)")
    print("2) Publicar mídia e gerar QR com link local")
    print("3) Adicionar QR Code (padrão ou artístico) em uma imagem")
    print("0) Sair")
    print("-" * 50)

def main():
    actions = {
        "1": action_generate_qr,
        "2": action_media_qr_local,
        "3": action_add_watermark_qr,
    }
    try:
        while True:
            print_menu()
            choice = prompt("Escolha uma opção: ").strip()

            if choice == "0":
                break

            action = actions.get(choice)
            if action:
                action()
            else:
                print("Opção inválida. Tente novamente.")
    finally:
        print("Encerrando servidor local (se ativo)...")
        stop_local_server()
        print("Programa finalizado.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nSaindo...")
        sys.exit(0)