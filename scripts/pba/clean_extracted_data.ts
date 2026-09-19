import fs from 'fs';
import path from 'path';

interface PbaNorma {
    titulo: string;
    url: string;
    preview_texto: string;
    texto_completo: string;
    tipo_norma: string;
    numero_norma: string;
    anio: number;
    page: number;
}

async function cleanAndSaveData() {
    const inputPath = path.join(process.cwd(), 'data', 'pba', 'salud_extracted.json');
    const outputPath = path.join(process.cwd(), 'data', 'pba', 'salud_cleaned.json');

    // Read raw data
    const rawData = JSON.parse(fs.readFileSync(inputPath, 'utf-8')) as PbaNorma[];

    console.log(`📚 Reading ${rawData.length} norms from extracted file`);

    // Clean each norma
    const cleanedData: PbaNorma[] = [];

    for (const norma of rawData) {
        // Remove markdown code blocks (```json ... ```)
        let cleanedText = norma.texto_completo;

        // Remove ```json at start if present
        if (cleanedText.startsWith('```json')) {
            cleanedText = cleanedText.replace('```json', '').trim();
        }

        // Remove ``` at end if present
        if (cleanedText.endsWith('```')) {
            cleanedText = cleanedText.replace(/```$/, '').trim();
        }

        // Clean up extra whitespace
        cleanedText = cleanedText.replace(/\n\s*\n/g, '\n').trim();

        // Add cleaned text back
        cleanedData.push({
            ...norma,
            texto_completo: cleanedText
        });
    }

    // Save cleaned data
    fs.writeFileSync(outputPath, JSON.stringify(cleanedData, null, 2));

    console.log(`✅ Saved ${cleanedData.length} cleaned norms to: ${outputPath}`);

    // Show statistics
    console.log('\n📊 Statistics:');
    console.log(`  Total norms: ${cleanedData.length}`);
    console.log(`  Unique types: ${[...new Set(cleanedData.map(d => d.tipo_norma))].join(', ')}`);
    console.log(`  Years: ${[...new Set(cleanedData.map(d => d.anio))].sort((a, b) => a - b).join(', ')}`);

    // Sample article extraction from first norma
    const firstNorm = cleanedData[0];
    if (firstNorm.texto_completo) {
        console.log(`\n📝 Sample from first norma "${firstNorm.titulo}":`);
        console.log(firstNorm.texto_completo.substring(0, 500) + '...');
    }

    return cleanedData;
}

async function main() {
    console.log('🧹 Cleaning extracted data...\n');
    await cleanAndSaveData();
    console.log('\n✅ Cleaning completed!');
}

main().catch(console.error);
