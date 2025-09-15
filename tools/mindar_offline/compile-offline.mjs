// tools/mindar_offline/compile-offline.mjs
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { loadImage } from 'canvas';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Importa OfflineCompiler a partir do pacote 'mind-ar' (repo GitHub)
async function importOfflineCompiler() {
    const candidates = [
        'mind-ar/src/image-target/offline-compiler.js',
        'mind-ar-js/src/image-target/offline-compiler.js' // fallback, se o alias/pacote variar
    ];
    let lastErr = null;
    for (const c of candidates) {
        try {
            const mod = await import(c);
            if (mod?.OfflineCompiler) return mod.OfflineCompiler;
        } catch (e) { lastErr = e; }
    }
    throw new Error(
        'Falha ao importar OfflineCompiler. Confirme a dependência "mind-ar" (via GitHub) e se expõe src/image-target/offline-compiler.js.\n' +
        (lastErr ? `Último erro: ${String(lastErr)}` : '')
    );
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
        // node-canvas: caminho é relativo ao CWD onde o Node foi executado (igual ao exemplo do repo)
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
        // Importa um .mind existente e reexporta (útil p/ validar/inspecionar)
        const buf = fs.readFileSync(inputs[0]);
        const arrBuf = buf.buffer.slice(buf.byteOffset, buf.byteOffset + buf.byteLength);
        compiler.importData(arrBuf);
    } else {
        const images = await loadImages(inputs);
        await compiler.compileImageTargets(images, (p) => {
            process.stdout.write(`\rProgresso: ${p.toFixed(2)}%   `);
        });
    }

    const out = compiler.exportData(); // ArrayBuffer/Buffer
    const outBuf = Buffer.isBuffer(out) ? out : Buffer.from(new Uint8Array(out));
    fs.writeFileSync(output, outBuf);
    process.stdout.write(`\n✅ .mind gerado: ${path.resolve(output)}\n`);
})().catch((err) => {
    console.error('\n❌ Erro ao compilar .mind:', err?.stack || err);
    process.exit(1);
});
