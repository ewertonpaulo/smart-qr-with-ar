import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { loadImage } from 'canvas';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function importOfflineCompiler() {
    try {
        const { OfflineCompiler } = await import('mind-ar/src/image-target/offline-compiler.js');
        return OfflineCompiler;
    } catch (e) {
        console.error('Failed to import OfflineCompiler from your fork.', e);
        throw new Error(
            'Could not load OfflineCompiler. Check if the "mind-ar" package is installed correctly.'
        );
    }
}

function parseArgs(argv) {
    const inputs = [];
    let output = null;
    for (let i = 2; i < argv.length; i++) {
        const a = argv[i];
        if ((a === '-i' || a === '--input') && argv[i + 1]) inputs.push(argv[++i]);
        else if ((a === '-o' || a === '--output') && argv[i + 1]) output = argv[++i];
        else if (a === '-h' || a === '--help') {
            console.log('Uso: node compile-offline.mjs -i <img1> [-i <img2> ...] -o <targets.mind>');
            process.exit(0);
        }
    }
    if (!inputs.length || !output) {
        console.error('Ex.: node compile-offline.mjs -i ./card.png -i ./logo.jpg -o ./targets.mind');
        process.exit(2);
    }
    return { inputs, output };
}

async function loadImages(paths) {
    const imgs = [];
    for (const p of paths) {
        const img = await loadImage(p);
        imgs.push(img);
    }
    return imgs;
}

(async () => {
    const { inputs, output } = parseArgs(process.argv);
    const OfflineCompiler = await importOfflineCompiler();

    const isSingleMind = inputs.length === 1 && inputs[0].toLowerCase().endsWith('.mind');

    const compiler = new OfflineCompiler();

    if (isSingleMind) {
        const buf = fs.readFileSync(inputs[0]);
        const arrBuf = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
        compiler.importData(arrBuf);
    } else {
        const images = await loadImages(inputs);
        await compiler.compileImageTargets(images, (p) => {
            process.stdout.write(`\rProgress: ${p.toFixed(2)}%   `);
        });
    }

    const out = compiler.exportData();
    const outBuf = Buffer.isBuffer(out) ? out : Buffer.from(new Uint8Array(out));
    fs.writeFileSync(output, outBuf);
    process.stdout.write(`\n✅ .mind generated: ${path.resolve(output)}\n`);
})().catch((err) => {
    console.error('\n❌ Failed to generate the .mind file:', err?.stack || err);
    process.exit(1);
});
