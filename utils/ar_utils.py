from pathlib import Path
import subprocess

MINDAR_OFFLINE_DIR = Path("tools/mindar_offline").resolve()

def generate_mind_file(image_path: Path) -> Path | None:
    """
    Gera um arquivo `.mind` a partir de uma imagem usando o OfflineCompiler (Node 18 + node-canvas).
    CLI esperado: tools/mindar_offline/compile-offline.mjs
    """
    print("\n🤖 Gerando marcador .mind com MindAR OfflineCompiler...")

    compiler_script = MINDAR_OFFLINE_DIR / "compile-offline.mjs"
    if not compiler_script.exists():
        print(f"❌ Não encontrei {compiler_script}. Verifique a estrutura em tools/mindar_offline e rode npm install.")
        return None

    output_path = image_path.with_suffix(".mind")
    command = [
        "node", str(compiler_script),
        "-i", str(image_path.resolve()),
        "-o", str(output_path.resolve())
    ]

    try:
        run = subprocess.run(
            command, cwd=str(MINDAR_OFFLINE_DIR),
            check=True, capture_output=True, text=True
        )
        if run.stdout:
            print(run.stdout)
        if output_path.exists():
            print(f"✅ Arquivo .mind gerado: {output_path}")
            return output_path
        print("❌ O processo terminou sem gerar o arquivo .mind esperado.")
        return None
    except FileNotFoundError:
        print("❌ 'node' não encontrado no PATH. Instale Node.js (>= 18).")
        return None
    except subprocess.CalledProcessError as e:
        print("❌ Erro ao executar o compilador Offline do MindAR.")
        if e.stdout: print(e.stdout)
        if e.stderr: print(e.stderr)
        return None