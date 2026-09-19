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

async function clearDatabase() {
    console.log('🔥 Iniciando limpieza de tablas de Leyes PBA...');
    
    const client = await pool.connect();
    try {
        await client.query('BEGIN');
        
        console.log('  - Eliminando datos de pba_referencias...');
        await client.query('TRUNCATE TABLE pba_referencias RESTART IDENTITY CASCADE');
        
        console.log('  - Eliminando datos de pba_articulos...');
        await client.query('TRUNCATE TABLE pba_articulos RESTART IDENTITY CASCADE');
        
        console.log('  - Eliminando datos de pba_normas...');
        await client.query('TRUNCATE TABLE pba_normas RESTART IDENTITY CASCADE');

        await client.query('COMMIT');
        
        console.log('✅ Limpieza completada exitosamente.');

    } catch (error: any) {
        await client.query('ROLLBACK');
        console.error('❌ Error durante la limpieza de la base de datos:', error.message);
    } finally {
        client.release();
        await pool.end();
    }
}

clearDatabase().catch(console.error);
