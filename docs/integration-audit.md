# Auditoría de integración — 29 de septiembre de 2026

## Base y alcance

Rama `main`, árbol limpio al iniciar, HEAD `d89f9f6`. Sitio estático: 11 HTML
(incluye 404), CSS y JS compartidos, manifest, sitemap, robots, README y assets.
No había AGENTS.md, gestor de paquetes, build, lint ni pruebas en el repositorio.
La copia perdida no está disponible: la comparación es contra la solicitud y el
historial local, no una reconstrucción verificable de aquella copia.

Se preservan los cambios de Kenneth del 22 de septiembre: ocho eventos reales,
calendario oficial, detección de eventos pasados, fotografías y logos auténticos,
compresión de imágenes, artículo ICC y eliminación de PDFs y entradas ficticias.
La paleta vigente ya es navy/rojo/hueso/amarillo/azul; los nombres `--green` son
heredados, no indican que el sitio use una identidad verde.

## Clasificación inicial de cada apartado solicitado

| # | Requisito | Estado inicial | Evidencia / decisión |
|---|---|---|---|
| 1 | Seguridad | YA IMPLEMENTADO | Estado, rama, historial y árbol revisados; no descartar ni publicar. |
| 2 | Fases | YA IMPLEMENTADO | Auditoría antes de cambios; plan abajo. |
| 3 | Auditoría | YA IMPLEMENTADO | Leídos HTML, CSS, JS, config, README e historial; inventario de assets. |
| 4 | Objetivo institucional | YA IMPLEMENTADO | CTAs, programas, contacto, eventos y comunidad presentes. |
| 5 | Landing | IMPLEMENTADO PARCIALMENTE | Completa visualmente; eventos vencidos y tarjetas de artículos inexistentes. |
| 6 | Multipágina | YA IMPLEMENTADO | Las diez páginas solicitadas y 404 existen. |
| 7 | Navegación | IMPLEMENTADO PARCIALMENTE | Header/footer iguales; dropdown solo hover, falta estado y manejo de teclado móvil. |
| 8 | Responsive | IMPLEMENTADO PARCIALMENTE | Breakpoints existentes; revisar navegación, grids, campos y textos largos en navegador. |
| 9 | Sistema visual | YA IMPLEMENTADO | Variables, tipografía, botones, cards y grids; conservar identidad. |
| 10 | Programas | YA IMPLEMENTADO | ELEVATE, BIG & Little, podcast, internados, ICC, servicio y liderazgo. |
| 11 | Membership | YA IMPLEMENTADO | Beneficios, pasos, puntos, FAQ y contacto; no sustituir datos existentes por antiguos. |
| 12 | Sponsors | IMPLEMENTADO PARCIALMENTE | Logos reales; precios y beneficios aún marcados para ajustar al deck oficial. |
| 13 | EN/ES | IMPLEMENTADO PARCIALMENTE | data-en/data-es y persistencia; quedan cargos, eventos y etiquetas sin traducir; atributos HTML rotos en artículo. |
| 14 | Detección inicial | FALTA | getLang devuelve inglés si no hay storage; también persiste la selección automática. |
| 15 | Menú móvil | IMPLEMENTADO PARCIALMENTE | Abre/cierra por clic; falta aria-expanded, Escape y gestión del foco. |
| 16 | Preloader | EXISTE UNA IMPLEMENTACIÓN ACTUAL MEJOR | Bajó de 1300 a 300 ms; eliminar espera restante y dependencia de recursos externos. |
| 17 | Animación | IMPLEMENTADO PARCIALMENTE | Reveal/progreso/transiciones; reduced-motion no cubre parallax, contadores ni scroll JS. |
| 18 | Contadores | IMPLEMENTADO PARCIALMENTE | Valores en repo; arranque en cero y lectura animada; conservar cifras sin añadir otras. |
| 19 | Newsletter | IMPLEMENTADO PARCIALMENTE | FormSubmit real, activación pendiente; JSON success ignorado y mensaje promete confirmación inexistente. |
| 20 | Analytics | IMPLEMENTADO PARCIALMENTE | ID ficticio cargado en 11 páginas; clic de calendario etiquetado como RSVP. |
| 21 | FAQ | IMPLEMENTADO PARCIALMENTE | Botones nativos; respuestas ocultas solo visualmente y altura fija, falta ARIA. |
| 22 | Eventos | EXISTE UNA IMPLEMENTACIÓN ACTUAL MEJOR | Ocho registros oficiales, JSON-LD y pasado automático; extender traducción/filtros y portada. |
| 23 | SEO | IMPLEMENTADO PARCIALMENTE | Titles/descriptions/canonical/OG existentes; OG usa ilustraciones antiguas; Twitter solo card. |
| 24 | JSON-LD | IMPLEMENTADO PARCIALMENTE | Organization/FAQ/Event/Breadcrumb/BlogPosting presentes; logo apunta a hero ilustrativo. |
| 25 | Accesibilidad | IMPLEMENTADO PARCIALMENTE | Skip link, headings y focus existentes; links vacíos, tabs incompletos, contraste de focus/pasados. |
| 26 | Performance | EXISTE UNA IMPLEMENTACIÓN ACTUAL MEJOR | JPG optimizados, lazy backgrounds, preconnect; preservar y quitar solicitudes ficticias de GA. |
| 27 | Assets | IMPLEMENTADO PARCIALMENTE | Fotos/logos reales más stock Unsplash mostrado como fotos de programas; usar fotos auténticas o ilustración neutral. |
| 28 | Datos institucionales | YA IMPLEMENTADO | Correo, extensión 3800 y ADEM coinciden con repo actual; preservar. |
| 29 | Enlaces | IMPLEMENTADO PARCIALMENTE | Redes concretas; referencias engañosas a artículos y href escapados incorrectamente en data-en/es. |
| 30 | Pendientes | IMPLEMENTADO PARCIALMENTE | PDFs/internados pendientes explícitos; casos, auspicios y newsletter necesitan claridad. |
| 31 | Manifest | IMPLEMENTADO PARCIALMENTE | Iconos reales; rutas absolutas fallan en subcarpetas; no existe servicio offline. |
| 32 | Sitemap/robots | YA IMPLEMENTADO | Diez URLs reales y canonical coherente; 404 fuera del sitemap. |
| 33 | Blog/casos | IMPLEMENTADO PARCIALMENTE | Blog depurado; portada y relacionados siguen enlazando títulos inexistentes. Caso compuesto advertido solo al final. |
| 34 | Código | IMPLEMENTADO PARCIALMENTE | Vanilla JS con guards; completar comportamientos compartidos sin framework. |
| 35 | Validación | FALTA | No hay scripts; añadir comprobaciones de estructura y regresiones de interacción. |
| 36 | Git/commits | YA IMPLEMENTADO | Sin push; dejar cambios revisables sin commits automáticos. |
| 37 | Cambios mínimos | YA IMPLEMENTADO | Ediciones focalizadas; conservar assets y arquitectura. |
| 38 | Auditoría final | FALTA | Ejecutar tras implementación y registrar resultados. |
| 39 | Reporte | FALTA | Entregar archivos, pruebas, pendientes y estado Git al cerrar. |
| 40 | Integración | YA IMPLEMENTADO | Prioridad a la versión actual; ningún rollback de commits. |

## Plan de implementación

1. Extender `assets/main.js`: detección del navegador con prioridad a preferencia
   manual válida, traducción dinámica y etiquetas, menú, FAQ y tabs accesibles,
   reduced-motion, newsletter con respuesta verificada y tracking correcto.
2. Corregir contenidos puntuales: portada y enlaces relacionados, paquetes aún no
   confirmados, caso ilustrativo y testimonios asociados. Mantener programas,
   artículo ICC, puntos, junta, patrocinadores y calendario actuales.
3. Ajustar CSS de accesibilidad/responsive, metadata/logo, manifest relativo y
   configuración única para integraciones sin credenciales inventadas.
4. Validar HTML, assets, enlaces y fragmentos EN/ES, JSON-LD, navegación compartida,
   sitemap/robots y navegador en varios tamaños/idiomas/estados de integración.
5. Revisar diff e historial protegido; documentar límites y pendientes reales.

## Decisiones de contenido

- Los valores ya publicados de membresía, puntos y credenciales se conservan;
  no hay un padrón o informe adjunto que permita certificar su vigencia actual.
- `case.html` declara expresamente que es un compuesto ilustrativo. Sus cifras,
  personajes y testimonios no deben servir como prueba de resultados reales.
- Sponsors contiene una instrucción explícita de ajustar precios/beneficios al
  deck, eliminado por ser placeholder. Se sustituye la oferta no confirmada por
  consulta al equipo de Finanzas, sin alterar los logos y donación institucional.
- La integración de newsletter necesita confirmación de activación de la cuenta
  FormSubmit. No se enviarán correos ni formularios reales durante las pruebas.
- No hay comparación posible con la copia perdida ni verificación independiente
  de datos institucionales privados. No se inventarán datos para cubrirlos.

## Cierre

Las fases de implementación, validación y auditoría final están recogidas en
[integration-report.md](integration-report.md), con archivos exactos, resultados
y pendientes. Los estados de la tabla anterior describen la situación inicial;
se conservan como evidencia de por qué se hicieron las modificaciones.
