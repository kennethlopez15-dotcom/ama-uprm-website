/* Public site settings. Never put secrets here. */
window.AMA_CONFIG = Object.freeze({
  // Set a real GA4 Measurement ID to enable analytics; empty means no requests.
  analyticsId: '',
  // Form backend (e.g. a Formspree endpoint https://formspree.io/f/xxxx). Empty = forms fall back to a pre-filled email draft.
  formEndpoint: ''
});
