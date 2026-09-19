import { CONFIG } from './config.js';

/**
 * Utilidades del scraper
 */

export function sleep(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

export function formatPath(anio: string): string {
  return CONFIG.DIR_FORMAT.replace('{anio}', anio);
}

export function formatFileName(numero: number): string {
  return CONFIG.FILE_FORMAT.replace('{numero}', numero.toString());
}

export function validateUrl(url: string): boolean {
  try {
    new URL(url);
    return true;
  } catch {
    return false;
  }
}
