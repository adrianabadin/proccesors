import axios from 'axios';
import fs from 'fs';
import path from 'path';
import https from 'https';

const BASE_URL = 'https://normas.gba.gob.ar';

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

async function fetchHtmlWithProxy(url: string): Promise<string> {
    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            let data = '';

            res.on('data', (chunk) => {
                data += chunk;
            });

            res.on('end', () => {
                resolve(data);
            });
        }).on('error', (err) => {
            reject(err);
        });
    });
}

async function extractNormaDetails(norma: PbaNorma): Promise<PbaNorma> {
    try {
        console.log(`  📄 Extrayendo texto completo de: ${norma.titulo}`);

        // Fetch the HTML content
        const html = await fetchHtmlWithProxy(norma.url);

        // Use Groq to extract structured data
        const systemPrompt = await fs.promises.readFile(
            path.join(process.cwd(), 'prompts', 'extract_norma_pba_system.txt'),
            'utf-8'
        );

        const userPrompt = `HTML Content:\n\n${html.substring(0, 15000)}...`;

        const response = await axios.post(
            'https://api.groq.com/openai/v1/chat/completions',
            {
                model: 'gemma2-9b-it',
                messages: [
                    {
                        role: 'system',
                        content: systemPrompt
                    },
                    {
                        role: 'user',
                        content: userPrompt
                    }
                ],
                temperature: 0.3,
                max_tokens: 4000
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${process.env.GROQ_API_KEY}`
                }
            }
        );

        const content = response.data.choices[0].message.content;
        console.log(`  ✅ Extracción completada de: ${norma.titulo}`);

        // Return updated norma with extracted text
        return {
            ...norma,
            texto_completo: content
        };

    } catch (error) {
        console.error(`  ❌ Error extrayendo norma ${norma.titulo}:`, error);
        return norma; // Return original norma if extraction fails
    }
}

async function processAllNormas(inputPath: string, outputPath: string) {
    console.log('📚 Procesando normas con DeepSeek...');

    // Read raw data
    const rawData = JSON.parse(fs.readFileSync(inputPath, 'utf-8')) as PbaNorma[];

    console.log(`📊 Found ${rawData.length} normas to process`);

    // Process each norma
    const processedData = await Promise.all(
        rawData.map(norma => extractNormaDetails(norma))
    );

    // Save processed data
    fs.writeFileSync(outputPath, JSON.stringify(processedData, null, 2));
    console.log(`\n💾 Datos procesados guardados en: ${outputPath}`);
    console.log(`📊 Total normas procesadas: ${processedData.length}`);
}

async function main() {
    const inputPath = path.join(process.cwd(), 'data', 'pba', 'salud_raw.json');
    const outputPath = path.join(process.cwd(), 'data', 'pba', 'salud_extracted.json');

    if (!DEEPSEEK_API_KEY) {
        console.error('❌ DEEPSEEK_API_KEY not set in environment');
        process.exit(1);
    }

    await processAllNormas(inputPath, outputPath);
}

main().catch(console.error);
