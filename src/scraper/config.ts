/**
 * Configuración centralizada del scraper de ordenanzas
 */

export interface ScraperConfig {
  readonly BASE_URL: string;
  readonly PAGES: readonly string[];
  readonly USER_AGENT: string;
  readonly ACCEPT_LANGUAGE: string;
  readonly MAX_RETRIES: number;
  readonly RETRY_DELAY_MS: number;
  readonly REQUEST_DELAY_MS: number;
  readonly FILE_FORMAT: string;
  readonly DIR_FORMAT: string;
  readonly ANIO: string;
}

export const CONFIG: ScraperConfig = {
  BASE_URL: 'https://hcd.saladillo.gob.ar/proyectos/page1/',
  PAGES: ['', 'page/2/', 'page/3/', 'page/4/'],
  USER_AGENT: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  ACCEPT_LANGUAGE: 'es-ES,es;q=0.9,en;q=0.8',
  MAX_RETRIES: 3,
  RETRY_DELAY_MS: 2000,
  REQUEST_DELAY_MS: 1000,
  FILE_FORMAT: 'Ordenanza N° {numero}.txt',
  DIR_FORMAT: './{anio}/',
  ANIO: '2025',
};
