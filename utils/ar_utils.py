from pathlib import Path
import subprocess
from PIL import Image

MINDAR_OFFLINE_DIR = Path("tools/mindar_offline").resolve()

def generate_mind_file(image_path: Path, output_path: Path) -> Path | None:
    """
    Generates a `.mind` file from an image directly to the specified output path.
    Expected CLI: tools/mindar_offline/compile-offline.mjs
    """
    print("\n🤖 Generating .mind marker with MindAR OfflineCompiler...")

    compiler_script = MINDAR_OFFLINE_DIR / "compile-offline.mjs"
    if not compiler_script.exists():
        print(f"❌ Could not find {compiler_script}. Check the structure in tools/mindar_offline and run npm install.")
        return None

    output_path.parent.mkdir(parents=True, exist_ok=True)

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

def _create_fhd_version_if_needed(image_path: Path) -> Path:
    """
    Checks if an image is larger than FHD (1920x1080). If so, creates a
    resized temporary copy and returns its path. Otherwise, returns the original path.
    """
    FHD_SIZE = (1920, 1080)
    try:
        with Image.open(image_path) as img:
            if img.width > FHD_SIZE[0] or img.height > FHD_SIZE[1]:
                print(f"Image is larger than FHD. Creating a temporary resized version for MindAR compiler...")
                img_copy = img.copy()
                img_copy.thumbnail(FHD_SIZE, Image.Resampling.LANCZOS)

                # Use a more specific temp name to avoid conflicts
                temp_path = image_path.with_name(f"{image_path.stem}_fhd_temp.jpg")
                img_copy.convert("RGB").save(temp_path, "JPEG", quality=90)
                print(f"Temporary version saved to: {temp_path}")
                return temp_path
    except Exception as e:
        print(f"Warning: Could not check or resize image. Using original. Error: {e}")

    return image_path
