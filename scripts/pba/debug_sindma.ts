import { chromium } from 'playwright';
import fs from 'fs';

async function debugPageStructure() {
    console.log('🔍 Debugging SINDMA page structure...');

    const browser = await chromium.launch({ headless: false, slowMo: 500 });
    const page = await browser.newPage();

    // First navigate to a search results page
    const searchUrl = 'https://normas.gba.gob.ar/resultados?page=1&q%5Bwith_some_words%5D=Salud+P%C3%A1blica';
    console.log(`📄 Navigating to: ${searchUrl}`);
    await page.goto(searchUrl, { waitUntil: 'networkidle' });

    // Take a snapshot of the page
    const snapshot = await page.content();
    fs.writeFileSync('debug_snapshot.html', snapshot);

    // Look for key elements
    console.log('\n🔬 Looking for page structure...');

    // Try different possible selectors
    const possibleSelectors = [
        'div.card', 'div.result-item', 'div.search-result',
        'article', '[role="article"]',
        'div[role="generic"]', 'div.generic-card'
    ];

    for (const selector of possibleSelectors) {
        const count = await page.locator(selector).count();
        if (count > 0) {
            console.log(`✅ Selector found: "${selector}" (${count} elements)`);

            // Get first element's HTML
            const first = await page.locator(selector).first();
            const html = await first.innerHTML();
            console.log(`   First element HTML preview:\n   ${html.substring(0, 500)}...`);
        }
    }

    // Look for link structures
    console.log('\n🔗 Looking for link structures...');
    const linkHrefs = await page.locator('a[href^="/"]').all();
    console.log(`Found ${linkHrefs.length} links starting with "/"`);

    if (linkHrefs.length > 0) {
        console.log('\nSample links:');
        for (let i = 0; i < Math.min(5, linkHrefs.length); i++) {
            const link = linkHrefs[i];
            const href = await link.getAttribute('href');
            const text = await link.textContent();
            console.log(`   ${i + 1}. "${text}" -> ${href}`);
        }
    }

    // Look for headings
    console.log('\n📝 Looking for headings...');
    const headings = await page.locator('h1, h2, h3, h4').all();
    console.log(`Found ${headings.length} headings`);

    // Look for any text with "Ley", "Decreto", "Resolucion"
    console.log('\n🔍 Looking for norm types...');
    const normTypes = await page.locator('text=/Ley|Decreto|Resolucion/i').all();
    console.log(`Found ${normTypes.length} matches for norm types`);

    // Try to find cards containing norm types
    for (const normTypeMatch of normTypes) {
        const parent = await normTypeMatch.locator('..');
        const parentHtml = await parent.innerHTML();
        console.log(`\nNorm type text: "${await normTypeMatch.textContent()}"`);
        console.log(`Parent element HTML preview:\n   ${parentHtml.substring(0, 800)}...`);
    }

    console.log('\n💾 Snapshot saved to debug_snapshot.html');
    console.log('⏸️  Browser will stay open for 30 seconds for manual inspection...');

    await page.waitForTimeout(30000);

    await browser.close();
}

debugPageStructure().catch(console.error);
