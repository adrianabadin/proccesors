import { chromium } from 'playwright';
import { CONFIG } from './config.js';
import { ScraperLogger } from './logger.js';
import { LinkExtractor } from './link-extractor.js';
import { OrdinanceDownloader } from './ordinance-downloader.js';
import { sleep } from './utils.js';

/**
 * Scraper principal de ordenanzas con Playwright
 * Itera páginas 2, 3 y 4, descargando todas las ordenanzas disponibles
 */

async function main() {
  const logger = new ScraperLogger();
  const startTime = Date.now();

  console.log('='.repeat(60));
  console.log('🚀 SCRAPER DE ORDENANZAS - Playwright');
  console.log('='.repeat(60));

  console.log('📋 Configuración:');
  console.log(`   - Año: ${CONFIG.ANIO}`);
  console.log(`   - Páginas: ${CONFIG.PAGES.join(', ')}`);
  console.log(`   - Reintentos: ${CONFIG.MAX_RETRIES}`);
  console.log(`   - Formato: ${CONFIG.FILE_FORMAT}`);
  console.log('');

  // Inicializar Playwright
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  let totalOrdenanzas = 0;

  try {
    // Iterar páginas 1, 2, 3, 4
    for (const pageType of CONFIG.PAGES) {
      logger.logInfo(`Procesando ${pageType}`);

      const extractor = new LinkExtractor();
      const downloader = new OrdinanceDownloader();

      const links = await extractor.extractLinks(page, pageType, parseInt(pageType.replace('page', '')));

      logger.logInfo(`Enlaces encontrados: ${links.length}`);

      // Descargar cada ordenanza
      for (const link of links) {
        try {
          const data = await downloader.downloadOrdenanza(page, link);
          totalOrdenanzas++;
          logger.logSuccess(`Guardada`, data.numero.toString());
        } catch (error) {
          logger.logError(`Error en ${link.numero}`, error instanceof Error ? error : undefined, undefined, link.numero.toString());
          if (error instanceof Error && (error.message.includes('network') || error.message.includes('timeout'))) {
            // Reintentar para errores de red
            logger.logInfo('Continuando scraper a pesar de error de red');
            continue;
          } else {
            // Error fatal - continuar con siguiente
            logger.logError('Saltando ordenanza debido a error fatal');
          }
        }
      }

      if (links.length === 0) {
        logger.logInfo('No más enlaces, fin de iteración');
      }

      // Pequeño delay entre páginas
      if (pageType !== CONFIG.PAGES[CONFIG.PAGES.length - 1]) {
        await sleep(CONFIG.REQUEST_DELAY_MS);
      }
    }

    logger.logSummary(startTime);
  } finally {
    await browser.close();
  }
}

main().catch((error) => {
  console.error('\n❌ Error fatal en el scraper:');
  console.error(error);
  process.exit(1);
});
