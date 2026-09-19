import fs from 'fs';
import path from 'path';
import https from 'https';
import { Pool } from 'pg';

const BIGMODEL_API_KEY = '005ad7682c9b4bef823c59632771cafb.FgHv8ocQgLYhpttb';
const DATABASE_URL = 'postgresql://adrian:!DarthHobbit%25@thecodersteam.com:5432/ordenanzas';

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

interface PbaArticulo {
    numero: string;
    contenido: string;
    estado?: string;
}

interface PbaNormaConArticulos extends PbaNorma {
    articulos: PbaArticulo[];
}

async function fetchHtml(url: string): Promise<string> {
    return new Promise((resolve, reject) => {
        https.get(url, (res) => {
            let data = '';
            res.on('data', chunk => data += chunk);
            res.on('end', () => resolve(data));
        }).on('error', reject);
    });
}

async function extractArticulosFromText(texto: string): Promise<PbaArticulo[]> {
    // Extract articles from the JSON structure in texto_completo
    try {
        const jsonMatch = texto.match(/\{[\s\S]*\}/);
        if (jsonMatch) {
            const data = JSON.parse(jsonMatch[0]);
            const normaData = data.norma;

            if (normaData?.articulos && Array.isArray(normaData.articulos)) {
                return normaData.articulos.map((art: any) => ({
                    numero: art.numero || '1',
                    contenido: art.contenido || '',
                    estado: art.estado || null
                }));
            }
        }
    } catch (e) {
        // Ignore parsing errors
    }

    // If no JSON found, try to extract articles using regex
    // This is a fallback when BigModel doesn't return structured articles
    const articulos: PbaArticulo[] = [];

    // Look for article patterns like "Artículo 1", "Art. 1", "Art. 1 bis", etc.
    const articleRegex = /(?:Artículo?\s*)?(\d+(?:\s*[bis]|))/g;
    let match;

    while ((match = articleRegex.exec(texto)) !== null) {
        // Extract context around each article
        const startIdx = Math.max(0, match.index - 100);
        const endIdx = Math.min(texto.length, match.index + match[0].length + 200);
        let contexto = texto.substring(startIdx, endIdx).trim();

        articulos.push({
            numero: match[1].replace(/\s+/g, ''),
            contenido: contexto
        });
    }

    return articulos.length > 0 ? articulos : [{ numero: '1', contenido: texto.substring(0, 500) }];
}

async function generateEmbedding(text: string): Promise<number[]> {
    try {
        const response = await fetch('https://open.bigmodel.cn/api/paas/v4/embeddings', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${BIGMODEL_API_KEY}`
            },
            body: JSON.stringify({
                model: 'embedding-2',
                input: text.substring(0, 8191)
            })
        });

        const data = await response.json();
        return data.data[0].embedding;
    } catch (error: any) {
        console.error(`  ❌ Error generando embedding:`, error.message);
        return [];
    }
}

async function insertArticuloToDatabase(
    pool: any,
    normaId: string,
    articulo: PbaArticulo,
    index: number
): Promise<boolean> {
    const client = await pool.connect();

    try {
        await client.query('BEGIN');

        const result = await client.query(
            `INSERT INTO pba_articulos (
                norma_id, numero_articulo, orden, texto, embedding_articulo, created_at
            ) VALUES ($1, $2, $3, $4, $5, NOW())
            RETURNING id`,
            [
                normaId,
                articulo.numero,
                index,
                articulo.contenido.substring(0, 10000), // Limit text length
                await generateEmbedding(articulo.contenido)
            ]
        );

        await client.query('COMMIT');
        return true;
    } catch (error: any) {
        await client.query('ROLLBACK');
        console.error(`  ❌ Error guardando artículo ${articulo.numero}:`, error.message);
        return false;
    } finally {
        client.release();
    }
}

async function processArticulos(cleanedData: PbaNorma[]) {
    console.log(`\n📝 Generando artículos individuales...\n`);

    const pool = new Pool({
        connectionString: DATABASE_URL
    });

    try {
        let totalArticulos = 0;
        let successCount = 0;

        for (let i = 0; i < cleanedData.length; i++) {
            const norma = cleanedData[i];
            console.log(`📍 Procesando norma ${i + 1}/${cleanedData.length}: ${norma.titulo}`);

            // Extract articles from the norm
            const articulos = await extractArticulosFromText(norma.texto_completo);
            console.log(`  📄 Encontrados ${articulos.length} artículos`);

            // Insert each article to database
            for (let j = 0; j < articulos.length; j++) {
                const articulo = articulos[j];

                // Check if article already exists for this norma
                const checkResult = await pool.query(
                    `SELECT id FROM pba_articulos WHERE norma_id = $1 AND numero_articulo = $2`,
                    [norma.titulo, articulo.numero] // Using titulo as simple identifier
                );

                if (checkResult.rows.length > 0) {
                    console.log(`  ⏭️  Artículo ${articulo.numero} ya existe, saltando`);
                    continue;
                }

                const inserted = await insertArticuloToDatabase(pool, norma.titulo, articulo, j);
                if (inserted) {
                    successCount++;
                    console.log(`  ✅ Artículo ${articulo.numero} guardado (ID: ${j + 1}/${articulos.length})`);
                }

                await new Promise(resolve => setTimeout(resolve, 300));
            }

            totalArticulos += articulos.length;

            if (i < cleanedData.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 1000));
            }
        }

        console.log(`\n📊 Resumen:`);
        console.log(`  ✅ Total normas procesadas: ${cleanedData.length}`);
        console.log(`  📄 Total artículos generados: ${totalArticulos}`);
        console.log(`  📈 Éxitos: ${successCount}`);

        // Verify articles in database
        const countResult = await pool.query('SELECT COUNT(*) FROM pba_articulos');
        console.log(`  Artículos en base de datos: ${countResult.rows[0].count}`);

    } catch (error: any) {
        console.error(`❌ Error en artículos:`, error.message);
    } finally {
        await pool.end();
    }
}

async function main() {
    console.log('🚀 Procesando artículos con BigModel embeddings\n');

    const inputPath = path.join(process.cwd(), 'data', 'pba', 'salud_cleaned.json');

    const cleanedData = JSON.parse(fs.readFileSync(inputPath, 'utf-8')) as PbaNorma[];

    console.log(`📊 Found ${cleanedData.length} norms to process`);
    console.log(`🔗 Database: PostgreSQL with real[] arrays`);
    console.log(`🤖 Using BigModel GLM 4.7 Flash for embeddings`);

    await processArticulos(cleanedData);

    console.log('\n🎉 Proceso de artículos completado!');
}

main().catch(console.error);
