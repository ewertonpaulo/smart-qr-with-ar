from pathlib import Path
import subprocess

MINDAR_OFFLINE_DIR = Path("tools/mindar_offline").resolve()

def generate_mind_file(image_path: Path) -> Path | None:
    """
    Generates a `.mind` file from an image using the OfflineCompiler (Node 18 + node-canvas).
    Expected CLI: tools/mindar_offline/compile-offline.mjs
    """
    print("\n🤖 Generating .mind marker with MindAR OfflineCompiler...")

    compiler_script = MINDAR_OFFLINE_DIR / "compile-offline.mjs"
    if not compiler_script.exists():
        print(f"❌ Could not find {compiler_script}. Check the structure in tools/mindar_offline and run npm install.")
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
            print(f"✅ .mind file generated: {output_path}")
            return output_path
        print("❌ The process finished without generating the expected .mind file.")
        return None
    except FileNotFoundError:
        print("❌ 'node' not found in PATH. Please install Node.js (>= 18).")
        return None
    except subprocess.CalledProcessError as e:
        print("❌ Error executing the MindAR Offline compiler.")
        if e.stdout: print(e.stdout)
        if e.stderr: print(e.stderr)
        return None