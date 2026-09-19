import fs from 'fs';
import path from 'path';
import { Pool } from 'pg';
import axios from 'axios';
import 'dotenv/config';

const BIGMODEL_API_KEY = process.env.BIGMODEL_API_KEY;
const DATABASE_URL = process.env.DATABASE_URL;

if (!BIGMODEL_API_KEY || !DATABASE_URL) {
    console.error('❌ BIGMODEL_API_KEY o DATABASE_URL no configurados en .env');
    process.exit(1);
}

const pool = new Pool({
    connectionString: DATABASE_URL,
});

async function generateEmbedding(text: string): Promise<number[]> {
    try {
        const response = await axios.post(
            'https://open.bigmodel.cn/api/paas/v4/embeddings',
            {
                model: 'embedding-2',
                input: text.substring(0, 8191)
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${BIGMODEL_API_KEY}`
                }
            }
        );
        return response.data.data[0].embedding;
    } catch (error: any) {
        console.error(`  ❌ Error generando embedding:`, error.message);
        return [];
    }
}

async function populateGranularData() {
    console.log('🚀 Iniciando proceso de granularización (Artículos y Referencias) con split por índices...');
    
    const client = await pool.connect();
    try {
        const normasResult = await client.query(`
            SELECT n.id, n.titulo, n.texto_completo, n.cuerpo_normativo_limpio
            FROM pba_normas n
            LEFT JOIN pba_articulos a ON n.id = a.norma_id
            WHERE n.cuerpo_normativo_limpio IS NOT NULL AND a.id IS NULL
        `);
        
        const normas = normasResult.rows;
        console.log(`📊 Encontradas ${normas.length} normas para procesar.`);

        for (const norma of normas) {
            console.log(`\n📍 Norma: ${norma.titulo} (ID: ${norma.id})`);
            
            let bigModelParsed: any = null;
            try {
                bigModelParsed = JSON.parse(norma.texto_completo);
            } catch (e) {
                console.error(`  ⚠️ Error JSON BigModel en norma ${norma.id}`);
                continue;
            }

            const cleanText = norma.cuerpo_normativo_limpio;
            
            // --- NUEVA LÓGICA DE PARSEO POR ÍNDICES ---
            const articleRegex = /(ARTÍCULO|ARTICULO)\s*(\d+°?(\s+bis)?(\s+ter)?(\s+quater)?)\.?/gis;
            const matches = Array.from(cleanText.matchAll(articleRegex));
            
            const articulosDetectados: { numero: string, contenido: string }[] = [];

            if (matches.length > 0) {
                console.log(`  🔍 Detectados ${matches.length} marcadores de artículos.`);
                
                for (let i = 0; i < matches.length; i++) {
                    const currentMatch = matches[i];
                    const nextMatch = matches[i + 1];
                    
                    const numero = currentMatch[2].replace('°', '').trim();
                    const startIndex = currentMatch.index! + currentMatch[0].length;
                    const endIndex = nextMatch ? nextMatch.index : cleanText.length;
                    
                    const contenido = cleanText.substring(startIndex, endIndex).trim();
                    
                    if (contenido) {
                        articulosDetectados.push({ numero, contenido });
                    }
                }
            } else {
                console.log(`  ⚠️ Sin marcadores. Usando "Artículo Único".`);
                articulosDetectados.push({ numero: 'Único', contenido: cleanText });
            }

            // --- INSERCIÓN ---
            console.log(`  ✨ Insertando ${articulosDetectados.length} artículos...`);
            let orden = 1;
            for (const art of articulosDetectados) {
                console.log(`    🔔 Embedding Art. ${art.numero}...`);
                const embedding = await generateEmbedding(art.contenido);

                await client.query(
                    `INSERT INTO pba_articulos (
                        norma_id, numero_articulo, orden, texto, embedding_articulo,
                        created_at
                    ) VALUES ($1, $2, $3, $4, $5, NOW())`,
                    [norma.id, art.numero, orden, art.contenido, embedding.length > 0 ? embedding : null]
                );
                orden++;
                await new Promise(resolve => setTimeout(resolve, 150));
            }

            // --- REFERENCIAS ---
            const referencias = bigModelParsed.referencias_detectadas || [];
            if (referencias.length > 0) {
                console.log(`  🔗 Insertando ${referencias.length} referencias...`);
                for (const ref of referencias) {
                    const refRaw = `${ref.norma_destino_tipo || ''} ${ref.norma_destino_numero || ''}/${ref.norma_destino_anio || ''}`.trim();
                    await client.query(
                        `INSERT INTO pba_referencias (norma_origen_id, tipo_referencia, referencia_texto_raw, created_at)
                         VALUES ($1, $2, $3, NOW())`,
                        [norma.id, ref.tipo || 'CITA', refRaw || 'Referencia']
                    );
                }
            }
            console.log(`  ✅ Completada.`);
        }

    } catch (error: any) {
        console.error('❌ Error fatal:', error.message);
    } finally {
        client.release();
        await pool.end();
    }
}

populateGranularData().catch(console.error);
