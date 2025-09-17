## Using the `tools/mindar_offline` Compiler

The `tools/mindar_offline` directory contains a standalone Node.js script to add markers to images and compile into a `.mind` file, which is used by [MindAR](https://hiukim.github.io/mind-ar-js-doc/) for image tracking. [repository](https://github.com/hiukim/mind-ar-js)
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