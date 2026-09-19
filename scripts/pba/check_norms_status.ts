import { Pool } from 'pg';
import 'dotenv/config';

const DATABASE_URL = process.env.DATABASE_URL;

if (!DATABASE_URL) {
    console.error('❌ DATABASE_URL no configurado en .env');
    process.exit(1);
}

const pool = new Pool({
    connectionString: DATABASE_URL,
});

async function getNormaContent(normaId: string) {
    const client = await pool.connect();
    try {
        console.log(`🔍 Recuperando texto_completo para la norma con ID: ${normaId}...`);
        const result = await client.query(
            'SELECT texto_completo FROM pba_normas WHERE id = $1;',
            [normaId]
        );
        if (result.rows.length > 0) {
            console.log('--- Contenido de texto_completo ---');
            console.log(result.rows[0].texto_completo);
            console.log('-----------------------------------');
        } else {
            console.log('Norma no encontrada.');
        }
    } catch (error: any) {
        console.error('❌ Error al recuperar texto_completo:', error.message);
    } finally {
        client.release();
        await pool.end();
    }
}

getNormaContent('e9fe8493-102d-411a-be6e-1b678871ddfa').catch(console.error);
