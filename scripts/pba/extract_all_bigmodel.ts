import axios from 'axios';
import fs from 'fs';
import path from 'path';
import https from 'https';
import { JSDOM } from 'jsdom';

import 'dotenv/config';
const BIGMODEL_API_KEY = process.env.BIGMODEL_API_KEY;
const BASE_URL = 'https://normas.gba.gob.ar';

interface PbaNorma {
    titulo: string;
    url: string;
    preview_texto: string;
    texto_completo: string; // Will store BigModel's JSON output
    clean_text_for_articles: string; // New field to store clean text for local article parsing
    tipo_norma: string;
    numero_norma: string;
    anio: number;
    page: number;
}

async function fetchHtml(url: string): Promise<string> {
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

/**
 * Extracts clean text from the HTML of a norm, attempting to remove
 * boilerplate sections like "VISTO", "CONSIDERANDO", and signatures.
 * This clean text is specifically for local article parsing.
 */
function extractCleanTextFromHtml(html: string): string {
    const dom = new JSDOM(html);
    const document = dom.window.document;

    // Remove header and footer elements that are not part of the norm's body
    document.querySelectorAll('header, footer, nav, script, style, .sidebar, .share-buttons, .back-to-top').forEach(el => el.remove());

    // Target the main content area where the norm text is typically found
    let mainContentElement = document.querySelector('.norma-content') || document.body;
    let cleanText = mainContentElement.textContent || '';

    // Advanced cleaning using regex for common boilerplate phrases
    // These patterns are aggressive and aim to isolate the core legislative text
    cleanText = cleanText.replace(/LA PLATA,\s+\d+\s+de\s+\w+\s+de\s+\d{4}/gim, ''); // Date at the top
    cleanText = cleanText.replace(/VISTO el expediente[\s\S]*?Y CONSIDERANDO:?/gim, ''); // VISTO and CONSIDERANDO sections
    cleanText = cleanText.replace(/Por ello,[\s\S]*?(EL GOBERNADOR|EL PRESIDENTE) DE LA PROVINCIA DE BUENOS AIRES[\s\S]*(DECRETA|PROMULGA|SANCIONA):?/gim, ''); // Governor's intro
    cleanText = cleanText.replace(/Registrar, comunicar y dar al SINDMA[\s\S]*?(AXEL KICILLOF|MARIA EUGENIA VIDAL|DANIEL SCIOLI|FIRMANTES)/gim, ''); // Signatures and closing instructions

    // Remove any remaining HTML tags that might have been converted to text
    cleanText = cleanText.replace(/<[^>]*>?/gm, '');

    // Remove multiple newlines and extra spaces
    cleanText = cleanText.replace(/(\r\n|\r|\n){2,}/g, '\n\n').trim();
    cleanText = cleanText.replace(/\s{2,}/g, ' '); // Replace multiple spaces with a single space

    return cleanText;
}


async function extractNormaDetailsWithBigModel(norma: PbaNorma): Promise<PbaNorma> {
    try {
        console.log(`  📄 Extrayendo contenido y metadatos de: ${norma.titulo}`);

        const html = await fetchHtml(norma.url);
        
        // Extract clean text from HTML for local article parsing later
        const cleanText = extractCleanTextFromHtml(html);

        // Limit the clean text for the BigModel API to avoid exceeding token limits
        // Send only a portion of cleanText to BigModel for metadata, refs, and summary
        const userPromptForBigModel = `Texto de la norma (limpio):\n\n${cleanText.substring(0, 10000)}...`; // Adjust as needed, 10k chars is about 2.5k tokens

        const systemPrompt = await fs.promises.readFile(
            path.join(process.cwd(), 'prompts', 'extract_norma_pba_system.txt'),
            'utf-8'
        );

        console.log(`  🔧 Calling BigModel API (GLM 4.7 Flash) with clean text for metadata...`);

        const response = await axios.post(
            'https://open.bigmodel.cn/api/paas/v4/chat/completions',
            {
                model: 'glm-4-flash',
                messages: [
                    {
                        role: 'system',
                        content: systemPrompt
                    },
                    {
                        role: 'user',
                        content: userPromptForBigModel
                    }
                ],
                temperature: 0.3,
                max_tokens: 4000,
                response_format: { type: "json_object" } // Ensure JSON output
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${BIGMODEL_API_KEY}`
                }
            }
        );

        const bigModelOutput = response.data.choices[0].message.content;
        console.log(`  ✅ Extracción de metadatos/resumen completada para: ${norma.titulo}`);

        return {
            ...norma,
            texto_completo: bigModelOutput, // Store BigModel's JSON output
            clean_text_for_articles: cleanText // Store the raw clean text separately
        };

    } catch (error: any) {
        console.error(`  ❌ Error extrayendo norma ${norma.titulo}:`, error.message);
        if (error.response) {
            console.error(`     Status: ${error.response.status}`);
            console.error(`     Data: ${JSON.stringify(error.response.data)}`);
        }
        return norma; // Return original norma if extraction fails
    }
}

async function processAllNormas(inputPath: string, outputPath: string) {
    console.log('📚 Procesando normas con BigModel GLM 4.7 Flash...');

    const rawData = JSON.parse(fs.readFileSync(inputPath, 'utf-8')) as PbaNorma[];
    console.log(`📊 Found ${rawData.length} normas to process`);

    const processedData: PbaNorma[] = [];
    for (let i = 0; i < rawData.length; i++) {
        const norma = rawData[i];
        console.log(`\n📍 Procesando norma ${i + 1}/${rawData.length}: ${norma.titulo}`);

        const result = await extractNormaDetailsWithBigModel(norma);
        processedData.push(result);

        await fs.promises.writeFile(
            outputPath,
            JSON.stringify(processedData, null, 2)
        );
        console.log(`  💾 Guardado progreso: ${i + 1}/${rawData.length}`);

        await new Promise(resolve => setTimeout(resolve, 1000));
    }

    fs.writeFileSync(outputPath, JSON.stringify(processedData, null, 2));
    console.log(`\n💾 Datos procesados guardados en: ${outputPath}`);
    console.log(`📊 Total normas procesadas: ${processedData.length}`);
}

async function main() {
    const inputPath = path.join(process.cwd(), 'data', 'pba', 'salud_raw.json');
    const outputPath = path.join(process.cwd(), 'data', 'pba', 'salud_extracted.json');

    if (!BIGMODEL_API_KEY) {
        console.error('❌ BIGMODEL_API_KEY not set');
        process.exit(1);
    }

    console.log('🚀 Starting BigModel GLM 4.7 Flash extraction pipeline with new clean text approach...\n');
    await processAllNormas(inputPath, outputPath);
    console.log('\n✅ Pipeline completed successfully!');
}

main().catch(console.error);