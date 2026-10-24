/* Public site settings. Never put secrets here. */
window.AMA_CONFIG = Object.freeze({
  // Set a real GA4 Measurement ID to enable analytics; empty means no requests.
  analyticsId: 'G-Q241V67CY6',
  // Form backend (e.g. a Formspree endpoint https://formspree.io/f/xxxx). Empty = forms fall back to a pre-filled email draft.
  formEndpoint: '',
  // RUMi chat assistant: URL of the Cloudflare Worker in worker/ (e.g. https://rumi.<account>.workers.dev).
  // Empty = RUMi still works, answering from assets/rumi/kb.json and free public APIs.
  rumiEndpoint: '',
  // Date shown as "Last updated" in every footer (YYYY-MM-DD). Bump it whenever site content changes.
  siteUpdated: '2026-10-24'
});
