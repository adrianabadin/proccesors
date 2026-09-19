import { CONFIG } from './config.js';

/**
 * Sistema de logging simple para el scraper
 */

export class ScraperLogger {
  private stats = {
    totalPages: 0,
    pagesProcessed: 0,
    ordinancesDownloaded: 0,
    errors: 0,
  };

  logInfo(message: string, page?: number, ordenanza?: string): void {
    this.stats.pagesProcessed++;
    console.log(`[INFO] ${message}${page ? ` [Página ${page}]` : ''}${ordenanza ? ` [${ordenanza}]` : ''}`);
  }

  logError(message: string, error?: Error, page?: number, ordenanza?: string): void {
    this.stats.errors++;
    console.error(`[ERROR] ${message}${page ? ` [Página ${page}]` : ''}${ordenanza ? ` [${ordenanza}]` : ''}`);
    if (error) {
      console.error(error.stack);
    }
  }

  logSuccess(message: string, ordenanza?: string, page?: number): void {
    this.stats.ordinancesDownloaded++;
    console.log(`✓ ${message}${ordenanza ? ` [${ordenanza}]` : ''}${page ? ` [Página ${page}]` : ''}`);
  }

  logSummary(startTime: number): void {
    const elapsed = Date.now() - startTime;
    const elapsedStr = (elapsed / 1000).toFixed(2);
    const rate = this.stats.totalPages > 0 ? (this.stats.ordinancesDownloaded / elapsed).toFixed(2) : '0';

    console.log('\n' + '='.repeat(60));
    console.log('📊 RESUMEN DE SCRAPING');
    console.log('='.repeat(60));
    console.log(`⏱️  Tiempo total: ${elapsedStr} segundos`);
    console.log(`📄 Páginas procesadas: ${this.stats.pagesProcessed}/${this.stats.totalPages}`);
    console.log(`📝 Ordenanzas descargadas: ${this.stats.ordinancesDownloaded}`);
    console.log(`❌ Errores: ${this.stats.errors}`);
    console.log(`🚀 Velocidad: ${rate} ordenanzas/segundo`);
    console.log('='.repeat(60) + '\n');
  }

  getErrorsCount(): number {
    return this.stats.errors;
  }

  getDownloadedCount(): number {
    return this.stats.ordinancesDownloaded;
  }
}
