# AMA UPRM — sitio web

Sitio estático (HTML/CSS/JS). No requiere build ni servidor.

## Estructura
- index.html, about.html, elevate.html, programs.html, events.html, membership.html, sponsors.html, blog.html
- assets/style.css — colores de marca en las variables al inicio (--green, --gold...)
- assets/main.js — animaciones, menú, toggle EN/ES, FAQ, filtros, newsletter
- Los 4 PDFs placeholder (Chapter Plan, Annual Report, deck de auspicio, guía de puntos) se eliminaron: contenían literalmente el texto "placeholder, replace this file" y un juez podía descargarlos. Los botones que los enlazaban ahora dicen "Coming soon" o piden el documento por correo. Cuando haya PDFs reales, subirlos a `assets/` con esos mismos nombres y volver a enlazarlos en about.html, sponsors.html y membership.html.

## Idioma
Todo texto con `data-en` / `data-es` se traduce con el botón EN/ES. Para editar un texto, cambia ambos atributos y el contenido visible.

## Reemplazar placeholders
- Fotos: cada `<div class="ph">` es un placeholder. Sustituir por `<img src="..." alt="...">` o añadir `style="background-image:url(...)"`.
- Logos de sponsors: `.logo-box` → `<a href><img></a>`.
- Newsletter: ya conectado a FormSubmit.co (`action="https://formsubmit.co/ama@uprm.edu"`), sin necesidad de cuenta. **Pendiente**: la primera persona que se suscriba en producción dispara un correo de activación a `ama@uprm.edu` — hay que abrirlo y confirmar una vez, o no llegan los envíos siguientes. Si se prefiere Mailchimp/Brevo más adelante, basta con cambiar el `action` del form.
- Instagram: enlazar cada `.ig` al post real.
- og:image: subir assets/og-image.jpg (1200×630).

## Publicar
GitHub Pages: subir la carpeta `site/` a un repo, Settings → Pages → branch main / root. Luego apuntar amauprm.org con un CNAME.
Netlify: arrastrar la carpeta `site/` a app.netlify.com/drop.

## Analytics (Google Analytics 4)
Cada página ya trae el snippet de GA4 en el `<head>` con un ID de ejemplo (`G-XXXXXXXXXX`). Para activarlo:
1. Crea una propiedad gratis en https://analytics.google.com (Admin → Crear propiedad) y copia tu Measurement ID (empieza con `G-`).
2. Reemplaza las dos apariciones de `G-XXXXXXXXXX` por tu ID real en las 11 páginas HTML (búscalo y reemplázalo en el editor, o pide ayuda para hacerlo de una vez).
3. `assets/main.js` ya envía 4 eventos personalizados que sirven como KPIs listos para reportar en GA4: `membership_interest_click` (clics en "Join Us"), `event_rsvp_click` (clics en RSVP, con el nombre del evento), `sponsor_package_click` (clics en paquetes de auspicio) y `newsletter_signup`. No requieren configuración adicional una vez el Measurement ID esté activo.

## Fotos
Las fotos de personas vienen de Unsplash (licencia Unsplash, uso libre) y se cargan desde su CDN; debajo de cada una hay una ilustración local de respaldo (`assets/img/`) por si el enlace falla. Para usar fotos propias, reemplaza el archivo local con el mismo nombre y borra la URL de Unsplash del `style="background-image:..."` (o deja solo el archivo local en `build.py` → `REMOTE`).
