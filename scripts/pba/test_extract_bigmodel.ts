import axios from 'axios';
import fs from 'fs';
import path from 'path';
import https from 'https';

const BIGMODEL_API_KEY = '005ad7682c9b4bef823c59632771cafb.FgHv8ocQgLYhpttb';
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

async function extractNormaDetailsWithGroq(norma: PbaNorma): Promise<PbaNorma> {
    try {
        console.log(`  📄 Extrayendo texto completo de: ${norma.titulo}`);

        // Fetch the HTML content
        const html = await fetchHtmlWithProxy(norma.url);
        console.log(`  📏 HTML length: ${html.length} characters`);

        // Use BigModel GLM 4.7 Flash to extract structured data
        const systemPrompt = await fs.promises.readFile(
            path.join(process.cwd(), 'prompts', 'extract_norma_pba_system.txt'),
            'utf-8'
        );

        const userPrompt = `HTML Content:\n\n${html.substring(0, 20000)}...`;

        console.log(`  🔧 Calling BigModel API (GLM 4.7 Flash)...`);

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
                        content: userPrompt
                    }
                ],
                temperature: 0.3,
                max_tokens: 4000
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${BIGMODEL_API_KEY}`
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

    } catch (error: any) {
        console.error(`  ❌ Error extrayendo norma ${norma.titulo}:`, error.message);
        if (error.response) {
            console.error(`     Status: ${error.response.status}`);
            console.error(`     Data: ${JSON.stringify(error.response.data)}`);
        }
        return norma; // Return original norma if extraction fails
    }
}

async function testSingleNorma() {
    const inputPath = path.join(process.cwd(), 'data', 'pba', 'salud_raw.json');
    const rawData = JSON.parse(fs.readFileSync(inputPath, 'utf-8')) as PbaNorma[];

    if (rawData.length === 0) {
        console.error('❌ No normas found in input file');
        return;
    }

    // Test with first norm
    const testNorma = rawData[0];
    console.log(`🧪 Testing extraction on: ${testNorma.titulo}`);
    console.log(`   URL: ${testNorma.url}`);
    console.log(`   Preview: ${testNorma.preview_texto.substring(0, 100)}...`);

    if (!BIGMODEL_API_KEY) {
        console.error('❌ BIGMODEL_API_KEY not set');
        return;
    }

    const result = await extractNormaDetailsWithGroq(testNorma);

    console.log('\n📊 Result:');
    console.log(`   Title: ${result.titulo}`);
    console.log(`   Type: ${result.tipo_norma}`);
    console.log(`   Number: ${result.numero_norma}`);
    console.log(`   Year: ${result.anio}`);
    console.log(`   Text length: ${result.texto_completo.length} characters`);
    console.log(`   Text preview: ${result.texto_completo.substring(0, 300)}...`);
}

async function main() {
    console.log('🚀 Starting BigModel API extraction test...\n');
    await testSingleNorma();
    console.log('\n✅ Test completed');
}

main().catch(console.error);
