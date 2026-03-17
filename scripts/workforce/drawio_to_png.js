#!/usr/bin/env node
// Renders each page/tab of a .drawio file to a separate PNG using draw.io's
// export service via Puppeteer.
//
// Usage: node drawio_to_png.js <input.drawio> <output_dir>
// Produces: output_dir/page-0.png, page-1.png, ...

const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

async function renderDrawio(inputFile, outputDir) {
  const xml = fs.readFileSync(inputFile, 'utf-8');

  // Parse diagram count from the XML
  const diagramMatches = xml.match(/<diagram[^>]*name="([^"]*)"[^>]*>/g) || [];
  const diagramNames = [...xml.matchAll(/<diagram[^>]*name="([^"]*)"[^>]*>/g)].map(m => m[1]);
  const pageCount = diagramMatches.length || 1;

  console.log(`Found ${pageCount} pages in ${inputFile}`);

  fs.mkdirSync(outputDir, { recursive: true });

  const browser = await puppeteer.launch({
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  for (let i = 0; i < pageCount; i++) {
    const page = await browser.newPage();
    await page.setViewport({ width: 1400, height: 900, deviceScaleFactor: 2 });

    // Use draw.io's export URL with the XML content
    const encodedXml = encodeURIComponent(xml);
    const url = `https://viewer.diagrams.net/export3.html`;

    await page.goto(url, { waitUntil: 'networkidle0', timeout: 30000 });

    // Send the diagram data to the viewer and request PNG export
    const pngData = await page.evaluate(async (xmlContent, pageIndex) => {
      return new Promise((resolve, reject) => {
        // Listen for the export result
        window.addEventListener('message', function handler(evt) {
          if (evt.data && evt.data.event === 'export') {
            window.removeEventListener('message', handler);
            resolve(evt.data.data);
          }
        });

        // Request export
        const msg = {
          action: 'export',
          format: 'png',
          xml: xmlContent,
          pageIndex: pageIndex,
          scale: 2,
          border: 10,
          background: '#ffffff'
        };
        window.postMessage(JSON.stringify(msg), '*');

        setTimeout(() => reject(new Error('Export timeout')), 15000);
      });
    }, xml, i).catch(() => null);

    if (pngData) {
      const buffer = Buffer.from(pngData.replace(/^data:image\/png;base64,/, ''), 'base64');
      const outFile = path.join(outputDir, `page-${i}.png`);
      fs.writeFileSync(outFile, buffer);
      console.log(`  Exported page ${i} (${diagramNames[i] || 'unnamed'}) -> ${outFile}`);
    } else {
      // Fallback: screenshot the viewer page with embedded diagram
      console.log(`  Falling back to screenshot for page ${i}...`);
      await page.goto(`https://viewer.diagrams.net/?highlight=0000ff&nav=1&page=${i}#R${encodeURIComponent(xml)}`, {
        waitUntil: 'networkidle0',
        timeout: 30000
      });
      await page.waitForTimeout(3000);

      const outFile = path.join(outputDir, `page-${i}.png`);
      await page.screenshot({ path: outFile, fullPage: true });
      console.log(`  Screenshot page ${i} (${diagramNames[i] || 'unnamed'}) -> ${outFile}`);
    }

    await page.close();
  }

  await browser.close();
  console.log('Done.');
  return diagramNames;
}

const [,, inputFile, outputDir] = process.argv;
if (!inputFile || !outputDir) {
  console.error('Usage: node drawio_to_png.js <input.drawio> <output_dir>');
  process.exit(1);
}

renderDrawio(inputFile, outputDir).catch(err => {
  console.error(err);
  process.exit(1);
});
