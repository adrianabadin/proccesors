import { CONFIG } from './config.js';
import { Page, OrdenanzaLink, OrdenanzaData } from './types.js';
import { sleep, formatPath, formatFileName } from './utils.js';
import * as fs from 'fs';
import * as path from 'path';
import { fileURLToPath } from 'url';
import { JSDOM } from 'jsdom';

/**
 * Descarga el contenido de ordenanzas usando Playwright
 */

export class OrdinanceDownloader {
  async downloadOrdenanza(
    page: Page,
    link: OrdenanzaLink,
    retries = 3
  ): Promise<OrdenanzaData> {
    try {
      await page.goto(link.url, {
        waitUntil: 'networkidle',
        timeout: 60000,
      });

      await page.waitForSelector('#content', { timeout: 10000 });

      const contenido = await page.$eval('#content', (el: any) => el.textContent);

      if (!contenido || contenido.trim().length === 0) {
        throw new Error('Contenido vacío');
      }

      const data: OrdenanzaData = {
        numero: link.numero,
        anio: link.anio,
        titulo: link.titulo,
        contenido: contenido.trim(),
        fechaDescarga: new Date().toISOString(),
      };

      await this.saveOrdenanza(data);
      return data;
    } catch (error) {
      if (retries <= 1) {
        throw error; // Reintentar si falla en el primer intento
      }
      return this.downloadOrdenanza(page, link, retries - 1);
    }
  }

  private async saveOrdenanza(data: OrdenanzaData): Promise<void> {
    const dirPath = formatPath(data.anio);

    if (!fs.existsSync(dirPath)) {
      fs.mkdirSync(dirPath, { recursive: true });
    }

    const fileName = formatFileName(data.numero);
    const filePath = path.join(dirPath, fileName);

    await fs.promises.writeFile(filePath, data.contenido, 'utf-8');
  }
}
