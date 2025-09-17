import os
from pathlib import Path
import subprocess
from PIL import Image

MINDAR_OFFLINE_DIR = Path("tools/mindar_offline").resolve()

def generate_mind_file(image_path: Path, output_path: Path) -> Path | None:
    print("\n Generating .mind marker with MindAR OfflineCompiler...")

    compiler_script = MINDAR_OFFLINE_DIR / "compile-offline.mjs"
    node_modules_dir = MINDAR_OFFLINE_DIR / "node_modules"

    if not node_modules_dir.is_dir():
        print("❌ Node.js dependencies not found in the tool directory!")
        print("   Please run the installation command to download the required packages.")
        print(f"\n   --> cd \"{MINDAR_OFFLINE_DIR}\" && npm install\n")
        return None

    processed_image_path = _create_img_light_version_if_needed(image_path)
    is_temp_image = processed_image_path != image_path

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        command = [
            "node", str(compiler_script),
            "-i", str(processed_image_path.resolve()),
            "-o", str(output_path.resolve())
        ]

        result = subprocess.run(
            command,
            cwd=str(MINDAR_OFFLINE_DIR),
            capture_output=True,
            text=True,
            check=False
        )

        if result.stdout:
            print(result.stdout.strip())
        if result.stderr:
            print("--- Errors ---")
            print(result.stderr.strip())

        if result.returncode == 0 and output_path.exists():
            print(f"\n✅ .mind file generated successfully: {output_path}")
            return output_path
        else:
            print(f"❌ The process failed with exit code {result.returncode}.")
            print("   Review the output above for errors from the Node.js script.")
            return None

    except FileNotFoundError:
        print("❌ 'node' command not found in your PATH.")
        print("   Please install Node.js (version 18.20.4 is recommended) and ensure it's accessible.")
        return None
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
        return None
    finally:
        if is_temp_image and processed_image_path.exists():
            try:
                os.remove(processed_image_path)
                print(f"Temporary file cleaned up: {processed_image_path}")
            except OSError as e:
                print(f"Warning: Could not remove temporary file. Error: {e}")

def _create_img_light_version_if_needed(image_path: Path) -> Path:
    FHD_WIDTH = 1920
    FHD_HEIGHT = 1080
    FHD_TOTAL_PIXELS = FHD_WIDTH * FHD_HEIGHT

    try:
        with Image.open(image_path) as img:
            image_total_pixels = img.width * img.height

            if image_total_pixels > FHD_TOTAL_PIXELS:
                img_copy = img.copy()
                img_copy.thumbnail((FHD_WIDTH, FHD_HEIGHT), Image.Resampling.LANCZOS)

                temp_path = image_path.with_name(f"{image_path.stem}_fhd_temp.jpg")
                img_copy.convert("RGB").save(temp_path, "JPEG", quality=90)
                return temp_path

    except Exception as e:
        print(f"Warning: Could not check or resize image. Using original. Error: {e}")

    return image_path
