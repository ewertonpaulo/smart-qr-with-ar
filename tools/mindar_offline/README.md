# compile-image-targets-flow

This mini project demonstrates the flow of the `compiler.compileImageTargets` function, which is part of an image processing pipeline for augmented reality applications. The project is structured to provide a clear understanding of how images are compiled into a format suitable for tracking in AR environments.

## Project Structure

```
compile-image-targets-flow
├── src
│   ├── index.ts          # Entry point of the application
│   ├── compiler.ts       # Contains the Compiler class and compileImageTargets method
│   └── types
│       └── index.ts      # Defines interfaces and types used in the project
├── package.json          # npm configuration file
├── tsconfig.json         # TypeScript configuration file
└── README.md             # Documentation for the project
```

## Setup

1. **Clone the repository:**
   ```
   git clone <repository-url>
   cd compile-image-targets-flow
   ```

2. **Install dependencies:**
   ```
   npm install
   ```

3. **Compile the TypeScript files:**
   ```
   npx tsc
   ```

4. **Run the application:**
   ```
   node dist/index.js
   ```

## Flow of `compiler.compileImageTargets`

The `compileImageTargets` function is the core of this project. Here’s a brief overview of its flow:

1. **Image Loading:** The function begins by loading an array of images that will be processed. This is done using the `loadImage` function, which creates an `Image` object for each file.

2. **Compilation Process:** Once the images are loaded, the `compileImageTargets` method is called with the array of images. This method processes each image to extract feature points and tracking information.

3. **Data Structure:** The result of the compilation is a structured data object that includes:
   - `trackingImageList`: A list of images that can be tracked.
   - `trackingData`: Information about the feature points detected in each image.
   - `imageList`: The original images that were processed.
   - `matchingData`: Data related to the matching points found in the images.

4. **Visualization:** After compilation, the results can be visualized, showing the feature points on the images, which helps in understanding how the tracking will work in an AR context.

5. **Exporting Data:** Finally, the compiled data can be exported to a file format suitable for use in AR applications.

## Conclusion

This project serves as a foundational example of how to compile image targets for augmented reality applications. By following the steps outlined above, you can set up the project and explore the functionality of the `compileImageTargets` method.