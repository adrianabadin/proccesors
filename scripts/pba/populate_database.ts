import fs from 'fs';
import path from 'path';
import https from 'https';
import { Pool } from 'pg';

import 'dotenv/config';
const BIGMODEL_API_KEY = process.env.BIGMODEL_API_KEY;
const DATABASE_URL = process.env.DATABASE_URL;

interface PbaNormaRaw {
    titulo: string;
    url: string;
    preview_texto: string;
    texto_completo: string; // BigModel's JSON output
    clean_text_for_articles: string; // Clean text for local article parsing
    tipo_norma: string;
    numero_norma: string;
    anio: number;
    page: number;
}

interface BigModelNormaOutput {
    norma: {
        tipo: string;
        numero: number;
        anio: number;
        fecha_sancion: string | null;
        fecha_publicacion: string | null;
        titulo: string;
        resumen: string;
        estado: string | null;
        organismo_emisor: string | null;
    };
    referencias_detectadas: Array<{
        tipo: string;
        norma_destino_tipo: string;
        norma_destino_numero: number;
        norma_destino_anio: number;
    }>;
    resumen_ejecutivo: string;
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

async function insertNormaToDatabase(pool: any, normaRaw: PbaNormaRaw) {
    const client = await pool.connect();

    try {
        await client.query('BEGIN');

        let bigModelParsed: BigModelNormaOutput;
        try {
            bigModelParsed = JSON.parse(normaRaw.texto_completo);
        } catch (e) {
            console.error(`  ⚠️ Error al parsear JSON de BigModel para ${normaRaw.titulo}. Saltando...`, e);
            await client.query('ROLLBACK');
            return null;
        }

        const normaData = bigModelParsed.norma;
        
        // Generate embedding for the executive summary
        const embedding = await generateEmbedding(bigModelParsed.resumen_ejecutivo);
        if (embedding.length === 0) {
            console.log(`  ⚠️ No se pudo generar embedding para el resumen ejecutivo, saltando`);
            await client.query('ROLLBACK');
            return null;
        }

        // Insertar norma en pba_normas
        const result = await client.query(
            `INSERT INTO pba_normas (
                tipo_norma, numero_norma, anio, fecha_sancion, fecha_publicacion,
                titulo, sintesis, texto_completo, cuerpo_normativo_limpio,
                embedding_resumen, url_boletin, estado, created_at, updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, NOW(), NOW())
            RETURNING id`,
            [
                normaData.tipo,
                normaData.numero.toString(), // Store as string for flexibility
                normaData.anio,
                normaData.fecha_sancion,
                normaData.fecha_publicacion,
                normaData.titulo,
                normaData.resumen, // Sintesis is BigModel's short summary
                normaRaw.texto_completo, // Store raw BigModel JSON output here
                normaRaw.clean_text_for_articles, // Store clean text for local article parsing
                embedding, // embedding_resumen
                normaRaw.url,
                normaData.estado || 'vigente',
            ]
        );

        const normaId = result.rows[0].id;
        console.log(`  ✅ Norma guardada con ID: ${normaId}`);
        console.log(`  ✅ Embedding de resumen guardado: ${embedding.length} dimensiones`);

        await client.query('COMMIT');

        return normaId;
    } catch (error: any) {
        await client.query('ROLLBACK');
        console.error(`  ❌ Error guardando norma ${normaRaw.titulo}:`, error.message);
        return null;
    } finally {
        client.release();
    }
}

async function saveNormasToDatabase(rawData: PbaNormaRaw[]) {
    console.log(`\n💾 Guardando ${rawData.length} normas en base de datos...\n`);

    const pool = new Pool({
        connectionString: DATABASE_URL
    });

    try {
        let successCount = 0;
        let failCount = 0;

        for (let i = 0; i < rawData.length; i++) {
            const norma = rawData[i];
            console.log(`📍 Procesando norma ${i + 1}/${rawData.length}: ${norma.titulo}`);

            const normaId = await insertNormaToDatabase(pool, norma);

            if (normaId) {
                successCount++;
            } else {
                failCount++;
            }

            // Small delay between insertions
            if (i < rawData.length - 1) {
                await new Promise(resolve => setTimeout(resolve, 500));
            }
        }

        console.log(`\n📊 Resumen:`);
        console.log(`  ✅ Éxitos: ${successCount}`);
        console.log(`  ❌ Fallos: ${failCount}`);
        console.log(`  📈 Total: ${rawData.length}`);

        // Verify with a test query
        console.log(`\n🔍 Verificando datos en base de datos...`);
        const testResult = await pool.query('SELECT COUNT(*) FROM pba_normas');
        console.log(`  Normas en base de datos: ${testResult.rows[0].count}`);

    } catch (error: any) {
        console.error(`❌ Error en database operations:`, error.message);
    } finally {
        await pool.end();
    }
}

async function main() {
    console.log('🚀 Populating database with BigModel embeddings\n');

    const inputPath = path.join(process.cwd(), 'data', 'pba', 'salud_extracted.json');

    const rawData = JSON.parse(fs.readFileSync(inputPath, 'utf-8')) as PbaNormaRaw[];

    console.log(`📊 Found ${rawData.length} norms to process`);
    console.log(`🔗 Database: PostgreSQL with real[] arrays (no pgvector)`);
    console.log(`🤖 Using BigModel GLM 4.7 Flash for embeddings`);

    await saveNormasToDatabase(rawData);

    console.log('\n🎉 Database population completed!');
}

main().catch(console.error);
