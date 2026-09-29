# AMA UPRM — sitio web

Sitio estático (HTML/CSS/JS), sin framework ni build. Para revisar todas las
funciones, servir la raíz por HTTP: `python -m http.server 8000 --bind 127.0.0.1`.
Abrir `http://127.0.0.1:8000/`. Con `file://`, la portada conserva un enlace al
calendario porque el navegador puede bloquear la lectura de `events.html`.

## Estructura
- index.html, about.html, elevate.html, programs.html, events.html, membership.html, sponsors.html, blog.html
- assets/style.css — navy, rojo, hueso, amarillo y azul en variables; `--green`
  es el nombre heredado del rojo de marca, no una indicación de color verde.
- assets/main.js — animaciones, menú, toggle EN/ES, FAQ, filtros, newsletter
- assets/config.js — configuración pública única para analytics y newsletter, sin secretos.
- blog-post.html, case.html y 404.html — artículo ICC, caso ilustrativo y error.
- docs/integration-audit.md — auditoría de los 40 apartados, evidencia y plan.
- scripts/validate.py y scripts/browser_checks.py — validación estática y pruebas de navegador.
- Los 4 PDFs placeholder (Chapter Plan, Annual Report, deck de auspicio, guía de puntos) se eliminaron: contenían literalmente el texto "placeholder, replace this file" y un juez podía descargarlos. Los botones que los enlazaban ahora dicen "Coming soon" o piden el documento por correo. Cuando haya PDFs reales, subirlos a `assets/` con esos mismos nombres y volver a enlazarlos en about.html, sponsors.html y membership.html.

## Idioma
El selector EN/ES usa `data-en` / `data-es`. Primero respeta `ama-lang` si contiene
`en` o `es`; sin preferencia válida recorre `navigator.languages`, luego usa
`navigator.language`, con inglés como fallback. Solo una selección manual se
guarda. Storage bloqueado no impide cambiar el idioma en la página actual.
Las etiquetas accesibles usan `data-aria-en` / `data-aria-es`.

Para editar contenido cambia ambos atributos y el texto visible. Dentro de un
atributo HTML usa `&quot;` para comillas y `&amp;` para ampersands; `\"` no es un
escape HTML. No pongas formularios ni controles con listeners dentro de un
elemento traducible: el contenido se sustituye con `innerHTML`.

## Reemplazar placeholders
- Fotos y logos: conservar los assets reales optimizados. `.ph.has-img` usa
  `data-bg` con carga diferida; `.ph` sin foto es una ilustración neutral.
- Newsletter: FormSubmit se conserva, **desactivado hasta verificar activación y
  entrega** a `ama@uprm.edu`. La persona responsable debe confirmar la activación
  y una prueba real antes de poner `newsletterEnabled: true` en `assets/config.js`.
  El formulario muestra su estado pendiente y el contacto mientras esté apagado.
  El éxito exige HTTP correcto y JSON `success: true` (booleano o cadena). No
  promete una suscripción automática ni un correo de confirmación al visitante.
  Cambiar de proveedor requiere adaptar también el contrato de respuesta en JS.
- Instagram: las dos imágenes reales enlazan al perfil oficial; faltan URLs de posts.
- Auspicios: publicar montos y beneficios únicamente con el deck aprobado.
- Casos: `case.html` y las tarjetas de ELEVATE son ejemplos ilustrativos; no
  reportar sus cifras como resultados reales. Los testimonios quedan pendientes.
- Las cifras institucionales y los puntos existentes se conservaron. Confirmar
  su vigencia con la junta antes de publicar cambios de semestre.
- El formulario de contacto abre una aplicación de correo; el usuario debe
  revisar y enviar allí. No tiene backend ni muestra un falso éxito.

## Publicar
Publicar la raíz de este repositorio en el alojamiento elegido. El dominio
canónico conservado es `https://www.amauprm.org`; no hay CNAME en este repo y
debe confirmarse DNS/alojamiento. No existe una carpeta `site/`.

El manifest usa rutas relativas y modo navegador. No existe service worker ni
funcionalidad offline. Para publicar en una subcarpeta, ajustar también el
`<base href="/">` de 404 a esa subcarpeta y revisar las URLs canónicas/sitemap.

## Analytics (Google Analytics 4)
Poner el Measurement ID real en `analyticsId` dentro de `assets/config.js`.
Vacío o de ejemplo: no carga GA ni envía eventos. No hay ID real en el repo.

Eventos: `membership_interest_click`, `sponsor_package_click`,
`newsletter_signup` (solo tras respuesta aceptada) y `event_calendar_click`.
`event_rsvp_click` queda reservado para un enlace de registro real marcado con
`data-analytics="event_rsvp_click"`; agregar al calendario no es registrarse.

## Fotos
Las páginas usan las fotos reales y logos ya presentes en `assets/img/`. Se
preservaron los archivos heredados aunque no todos están en uso. No existe
`build.py`. El logo de JSON-LD es `logo-full.png`; OG y Twitter usan fotos reales.

## Eventos y componentes compartidos

`events.html` es la fuente de las tarjetas. La portada lee hasta tres próximos
eventos desde esa página, sin una segunda lista manual. Mantener `id`,
`data-date="AAAA-MM-DD"`, categoría, EN/ES y JSON-LD al añadir actividades.
El pasado se calcula por día de Puerto Rico, no por la zona horaria del visitante.
La lista es una selección mantenida manualmente, no una sincronización con la API
de Google Calendar. El calendario embebido sigue mostrando la agenda oficial.

Header y footer permanecen en HTML para no depender de JS para navegar. El
validador comprueba que no diverjan; los comportamientos viven en un solo JS.

## Validación

Sin dependencias: `python scripts/validate.py`.

Pruebas ampliadas en un entorno temporal/virtual: instalar `playwright html5lib`,
tener Microsoft Edge instalado y ejecutar `python scripts/browser_checks.py`.
No se añaden dependencias al sitio. Las pruebas arrancan un servidor local,
interceptan servicios externos, comprueban ambas lenguas a 320, 390, 768, 1024 y
1440 px y guardan capturas en `.validation/` (ignorado por Git). No envían correos.
Para evaluar fuentes y embeds reales, hacer también una revisión con red;
la suite aislada no certifica disponibilidad de servicios externos.
