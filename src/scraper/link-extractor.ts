import { CONFIG } from './config.js';
import { Page, OrdenanzaLink } from './types.js';
import { sleep } from './utils.js';
import { JSDOM } from 'jsdom';

/**
 * Extrae enlaces de ordenanzas usando Playwright y JSDOM
 */

export class LinkExtractor {
  async extractLinks(page: Page, pageType: string, pageNum: number): Promise<OrdenanzaLink[]> {
    const url = `${CONFIG.BASE_URL}${pageType}?f1=${CONFIG.ANIO}&wpcfs=preset-1`;
    
    await page.goto(url, {
      waitUntil: 'networkidle',
      timeout: 30000,
    });
    
    const content = await page.content();
    const dom = new JSDOM(content);
    
    // Select all ordinance containers
    const ordinanceContainers = Array.from(dom.window.document.querySelectorAll('.h-column-container.ordenanza.type-ordenanza'));
    const links: OrdenanzaLink[] = [];
    
    for (const container of ordinanceContainers) {
      // Find the title link
      const titleLink = container.querySelector('.h-blog-title a');
      if (titleLink && titleLink.href) {
        const h4 = titleLink.querySelector('h4');
        const text = h4?.textContent;
        if (text) {
          const numero = this.extractNumero(text);
          if (numero) {
            links.push({
              url: titleLink.href,
              numero,
              anio: CONFIG.ANIO,
              titulo: text.trim(),
            });
          }
        }
      }
    }
    
    return links;
  }

  private extractNumero(text: string): number | null {
    const match = text.match(/Ordenanza N° (\d+)/);
    return match ? parseInt(match[1]) : null;
  }
}
