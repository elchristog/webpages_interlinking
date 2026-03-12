// @ts-check
import { defineConfig } from 'astro/config';
import sitemap from '@astrojs/sitemap';
import fs from 'fs';

// Read injected config to fetch the current dynamic domain during build time
let siteUrl = 'http://localhost:4321';
try {
  const configRaw = fs.readFileSync('./src/data/config_inyectada.json', 'utf-8');
  siteUrl = JSON.parse(configRaw).dominio || siteUrl;
} catch (e) {
  console.warn("Could not load injected domain, defaulting to localhost");
}

// https://astro.build/config
export default defineConfig({
  site: siteUrl,
  integrations: [sitemap()]
});