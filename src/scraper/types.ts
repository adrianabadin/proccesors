/**
 * Definiciones de tipos TypeScript para el scraper de ordenanzas
 */

import type { Page as PlaywrightPage } from 'playwright';

export interface OrdenanzaLink {
  readonly url: string;
  readonly numero: number;
  readonly anio: string;
  readonly titulo: string;
}

export interface OrdenanzaData {
  readonly numero: number;
  readonly anio: string;
  readonly titulo: string;
  readonly contenido: string;
  readonly fechaDescarga: string;
}

export type Page = PlaywrightPage;
