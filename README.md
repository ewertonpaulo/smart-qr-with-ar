# Smart QR Code Image Processor

This project is a Python-based command-line tool for adding various types of QR code watermarks to images. It allows you to embed simple text, link to locally hosted media, or create augmented reality "Live Photo" experiences using AR.

## Project Structure

```text
poc_smart_qr/
├── .venv/
├── example/                 # Example media files
├── public/                  # Served by the local web server
│   └── media/               # Where user media is copied
├── saved/                   # Output images are saved here
├── tools/
│   └── mindar_offline/      # Standalone Node.js tool for compiling .mind files
│       ├── compile-offline.mjs
│       └── package.json
├── utils/                   # Python utility modules
│   ├── ar_utils.py
│   ├── image_utils.py
│   ├── qr_utils.py
│   ├── shortid.py
│   └── utils.py
├── actions.py               # Core application logic for menu actions
├── local_server.py          # Simple threaded HTTP server
├── main.py                  # Main application entry point
├── requirements.txt
└── template_ar.html    # HTML template for the AR experience
```


## Features

1.  **Add QR Code to an image**: Embeds a simple QR code with user-defined text content onto an image.
2.  **Add a memory to an image**: Links a local media file (image or video) to the base image. It copies the media to a `public/media` directory, starts a local server, and embeds a QR code containing the local URL to that file.
3.  **Create 'Live Photo'**: Generates an augmented reality experience. It takes a target image and a video, compiles the target image into a `.mind` file for AR image tracking, and hosts an HTML page that overlays the video on the target image when viewed through a phone's camera.

## How to Run the Main Application

1.  **Install Python Dependencies**:
    ```bash
    python -m venv .venv
    ```
    ```bash
    .venv\Scripts\activate
    ```
    ```bash
    pip install -r requirements.txt
    ```

2.  **Run the Main Script**:
    ```bash
    python main.py
    ```

3.  **Follow the Menu Prompts**:
    The application will display a menu with the available options. Choose an option and provide the requested file paths and content.

    ```
    ==================================================
    Smart QR - Image Processor
    ==================================================
    1) Add QR Code to an image
    2) Add a memory to an image
    3) Create 'Live Photo'
    0) Exit
    --------------------------------------------------
    Choose an option:
    ```

## Using the `tools/mindar_offline` Compiler

The `tools/mindar_offline` directory contains a standalone Node.js script to add markers to images and compile into a `.mind` file, which is used by [MindAR](https://hiukim.github.io/mind-ar-js-doc/) for image tracking. [repository](https://github.com/hiukim/mind-ar-js)

**Recomended node version**:
``
    18.20.4 
``

1.  **Navigate to the Directory**:
    ```bash
    cd tools/mindar_offline
    ```

2.  **Install Node.js Dependencies**:
    ```bash
    npm install
    ```

3.  **Run the Compiler**:
    Use the `compile-offline.mjs` script with input (`-i`) and output (`-o`) flags. You can provide multiple input images.

    **Syntax**:
    ```bash
    node compile-offline.mjs -i <path/to/image1.jpg> -i <path/to/image2.png> -o <output/path/targets.mind>
    ```

    **Example**:
    ```bash
    node compile-offline.mjs -i ../../example/nepal_tree.png -o ../../public/media/custom.mind
    ```

## iOS and HTTPS Requirement for 'Live Photo'

When you create a 'Live Photo' (Option 3), the application generates a URL that links to your local server (e.g., `http://192.168.1.10:8000/experience.html`).

Modern mobile operating systems, especially **iOS**, require a secure `https://` connection to grant camera access in the web browser. Since the built-in server provides a standard `http://` link, you will not be able to open the camera to view the AR experience on an iPhone or iPad directly.

To solve this, you need to expose your local server to the internet through a secure tunnel. Tools like **ngrok** are perfect for this.

### How to use ngrok

1.  **Download and set up ngrok**: Follow the instructions on the [ngrok website](https://ngrok.com/).

2.  **Run the Python Project**: Start the `main.py` script. It will tell you which port the local server is running on (e.g., `8000`).

3.  **Start an ngrok Tunnel**: Open a new terminal and run the following command, replacing `8000` with the port your server is using:
    ```bash
    ngrok http 8000
    ```

4.  **Get the HTTPS URL**: ngrok will provide a public `https://` forwarding URL (e.g., `https://random-string.ngrok-free.app`).

5.  **Use the URL**: When running Option 3 in the script, it will generate a final URL. The script in `actions.py` is hardcoded with an example ngrok URL. You should modify the `ar_page_url` variable in `action_create_mindar_live_photo` to use the public URL provided by your ngrok session. You can then share this `https://` link or embed it in a new QR code to use the AR experience on any device, including iOS.