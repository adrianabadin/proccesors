import { chromium } from 'playwright';
import fs from 'fs';
import path from 'path';

interface PbaNorma {
    titulo: string;
    url: string;
    preview_texto: string;
    texto_completo: string | null;
    tipo_norma: string;
    numero_norma: string;
    anio: number;
    page: number;
}

const BASE_URL = 'https://normas.gba.gob.ar';
const SEARCH_QUERY = 'Salud+Pública'; // Mantendremos la búsqueda amplia, pero filtraremos después

async function runLimitedCrawl() {
    const TOTAL_PAGES = 5;
    const allResults: PbaNorma[] = [];
    
    console.log(`🚀 Iniciando crawl inteligente (primeras ${TOTAL_PAGES} páginas)...`);
    console.log(`🎯 Prioridad: Leyes > Resoluciones > Decretos`);

    const browser = await chromium.launch({ headless: true });
    const page = await browser.newPage();

    try {
        for (let i = 1; i <= TOTAL_PAGES; i++) {
            console.log(`\n📄 Procesando página ${i} de ${TOTAL_PAGES}...`);
            const url = `${BASE_URL}/resultados?page=${i}&q%5Bwith_some_words%5D=${encodeURIComponent(SEARCH_QUERY)}`;
            await page.goto(url, { waitUntil: 'networkidle' });

            const cards = await page.locator('.card').all();
            if (cards.length === 0) {
                console.log('⚠️ No se encontraron más resultados. Fin del crawl.');
                break;
            }

            console.log(`  ➜ ${cards.length} normas encontradas en la página.`);
            
            const pageResults: PbaNorma[] = [];
            for (const card of cards) {
                try {
                    const titleElement = await card.locator('h3.card-title.rule-name a').first();
                    const count = await titleElement.count();
                    if (count === 0) continue;

                    const titulo = (await titleElement.textContent())?.trim() || '';
                    const href = await titleElement.getAttribute('href');
                    
                    const normMatch = titulo.match(/^(Ley|Decreto|Resolucion)\s*(\d+)\/(\d{4})/i);
                    const tipo_norma = normMatch?.[1] || 'Desconocido';
                    
                    // Extraer el resto de la info
                    const fullUrl: string = href ? `${BASE_URL}${href}` : '';
                    const numero_norma = normMatch?.[2] || '0';
                    const anio = parseInt(normMatch?.[3] || '0');
                    const blockquote = await card.locator('blockquote').first();
                    const preview_texto: string = (await blockquote.count() > 0) ? (await blockquote.textContent())?.trim() || '' : '';

                    pageResults.push({
                        titulo, url: fullUrl, preview_texto, tipo_norma,
                        numero_norma, anio, page: i, texto_completo: ''
                    });

                } catch (err) {
                    console.error(`  ⚠️ Error extrayendo una tarjeta:`, err);
                }
            }

            // **LÓGICA DE PRIORIZACIÓN**
            const priority = { 'Ley': 1, 'Resolucion': 2, 'Decreto': 3, 'Desconocido': 4 };
            pageResults.sort((a, b) => (priority[a.tipo_norma] || 4) - (priority[b.tipo_norma] || 4));
            
            console.log(`  ✨ Página ordenada por prioridad. Añadiendo ${pageResults.length} normas al resultado final.`);
            allResults.push(...pageResults);

            await page.waitForTimeout(1500); // Delay para no saturar
        }

    } catch (error) {
        console.error('❌ Error fatal durante el crawl:', error);
    } finally {
        await browser.close();
    }

    // Guardar resultados crudos
    const outputPath = path.join(process.cwd(), 'data', 'pba', 'salud_raw.json');
    fs.writeFileSync(outputPath, JSON.stringify(allResults, null, 2));
    console.log(`\n💾 Resultados guardados en: ${outputPath}`);
    console.log(`📊 Total normas recolectadas y priorizadas: ${allResults.length}`);

    return allResults;
}

runLimitedCrawl().then(results => {
    if (results.length > 0) {
        console.log(`\n✅ Crawl completado. La primera norma en la lista es de tipo: "${results[0].tipo_norma}"`);
    } else {
        console.log('\n❌ Crawl completado sin resultados.');
    }
});
