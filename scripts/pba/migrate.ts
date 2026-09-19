
import pg from 'pg';
import fs from 'fs';
import path from 'path';
import 'dotenv/config';

const { Client } = pg;

async function migrate() {
    const client = new Client({
        connectionString: process.env.DATABASE_URL,
    });

    try {
        await client.connect();
        console.log('📦 Conectado a la base de datos para migración...');

        const sqlPath = path.join(process.cwd(), 'scripts', 'pba', 'setup_db.sql');
        const sql = fs.readFileSync(sqlPath, 'utf8');

        await client.query(sql);
        console.log('✅ Tablas de Legislación PBA creadas exitosamente.');

    } catch (err) {
        console.error('❌ Error durante la migración:', err);
    } finally {
        await client.end();
    }
}

migrate();
