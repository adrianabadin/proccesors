import pg from 'pg';
import fs from 'fs';
import path from 'path';
import 'dotenv/config';

const { Client } = pg;

async function recreateDatabase() {
    const client = new Client({
        connectionString: process.env.DATABASE_URL,
    });

    try {
        await client.connect();
        console.log('📦 Conectado a la base de datos para RECREACIÓN TOTAL...');

        // 1. Eliminar tablas existentes (en orden inverso de dependencia)
        console.log('🗑️ Eliminando tablas existentes...');
        await client.query('DROP TABLE IF EXISTS pba_referencias CASCADE');
        await client.query('DROP TABLE IF EXISTS pba_articulos CASCADE');
        await client.query('DROP TABLE IF EXISTS pba_normas CASCADE');

        // 2. Leer y ejecutar el archivo SQL
        const sqlPath = path.join(process.cwd(), 'scripts', 'pba', 'setup_db.sql');
        const sql = fs.readFileSync(sqlPath, 'utf8');

        console.log('🏗️ Creando tablas con el nuevo esquema...');
        await client.query(sql);
        
        // 3. Verificar que la columna crítica existe
        const checkColumn = await client.query(`
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'pba_normas' AND column_name = 'cuerpo_normativo_limpio'
        `);

        if (checkColumn.rows.length > 0) {
            console.log('✅ Verificación exitosa: La columna "cuerpo_normativo_limpio" existe.');
        } else {
            console.error('❌ Error: La columna "cuerpo_normativo_limpio" NO se creó.');
        }

        console.log('🚀 Base de datos PBA recreada exitosamente.');

    } catch (err) {
        console.error('❌ Error fatal durante la recreación:', err);
    } finally {
        await client.end();
    }
}

recreateDatabase();
