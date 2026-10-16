# Adaptación a dispositivos — 15 de octubre de 2026

## Implementación

- Se conservan las 11 páginas, contenido EN/ES, marca y arquitectura estática.
- El menú conserva el punto de cambio de 1200 px y también pasa a compacto si
  la fila de escritorio deja de caber por fuentes, traducciones o texto ampliado.
  Escape, foco, redimensionamiento y bloqueo del fondo siguen compartidos.
  Los submenús cerrados se marcan `inert` para impedir foco fuera de pantalla.
- Botones y controles principales tienen un área mínima de 44 × 44 CSS px.
  Los campos usan 16 px de base y pueden ampliarse; se permite que las etiquetas
  y botones largos ocupen varias líneas. Los efectos de hover requieren ratón.
- Se mantienen alturas dinámicas y desplazamiento del menú, con separación de
  áreas seguras. El botón de volver arriba se oculta al entrar un embed en el
  área visible para evitar cubrir controles externos.
- Diez ubicaciones de fotografías interiores usan imágenes HTML nativas con
  `srcset`, `sizes`, dimensiones y carga diferida. Funcionan sin JavaScript y
  mantienen recorte, proporción y nombres accesibles en ambos idiomas.
- Se generaron siete WebP: 480/960 px para la foto de grupo, 480/607 px para la
  delegación y 480/960/1200 px para el edificio. No hay originales con ancho
  suficiente para una variante de 1440 px de esas fotos; no se ampliaron.
- Se conservan la imagen prioritaria de portada, las alturas de embeds y sus
  enlaces alternativos. No se publica ni se despliega ningún cambio.

## Verificación reproducible

Ejecutar `python scripts/validate.py` y `python scripts/browser_checks.py
--browser <motor>` para `chromium`, `firefox` y `webkit`. Edge sigue disponible
como valor predeterminado. Las dependencias y navegadores son herramientas de
desarrollo, no dependencias del sitio.

Cada motor comprueba 924 casos adaptables: los cinco anchos originales, los
límites 559/560/561, 899/900/901, 1023/1024/1025 y 1199/1200/1201, y 1920 px;
EN/ES y movimiento normal/reducido. Se añaden 844 × 390 y 1024 × 600, texto al
200 % a 320 y 1201 px, tacto emulado, acceso al menú, campos enfocados,
protección de controles externos y fotografías sin JavaScript.

Las mediciones de texto excluyen decoraciones; los solapamientos se comprueban
entre componentes de las rejillas. No se presentan esas mediciones como una
auditoría exhaustiva de accesibilidad. Las animaciones finitas se llevan a su
estado final para medir; la suite funcional mantiene interacciones reales.

La revisión de red separada cubre siete páginas a 390 y 1440 px, además de mapa,
calendario y Spotify a 320 × 640 y 844 × 390. Desactiva la configuración de
analytics y de envíos, conserva la carga real de fuentes y terceros y registra
respuestas, fallos de red, geometría y capturas. Las capturas no certifican la
disponibilidad futura de servicios externos.

## Límites de la comprobación

- WebKit de Playwright no es una certificación de Safari en un iPhone físico.
- La ampliación de fuentes al 200 % y el viewport de 320 CSS px comprueban
  ampliación de texto y reflujo. El zoom nativo del navegador es una revisión
  manual adicional.
- Una pantalla baja aproxima el espacio disponible con teclado abierto, pero
  no reproduce un teclado virtual ni sus cambios de viewport en iOS/Android.
- Quedan pendientes pruebas físicas de Safari/iPhone y Chrome/Android: giro,
  teclado, menú, zoom, foco y formularios. No se enviarán formularios reales.

Los informes detallados y capturas se guardan en `.validation/` (ignorado por
Git). La entrega debe distinguir los resultados automatizados de estos pasos
manuales pendientes.

## Evidencia de la revisión

| Motor | Casos adaptables | Fallos |
| --- | ---: | ---: |
| Chromium | 924 | 0 |
| Firefox | 924 | 0 |
| WebKit | 924 | 0 |

La suite funcional conserva además sus 110 combinaciones por motor y sus 13
grupos de comprobación. Las pruebas físicas y el zoom nativo siguen pendientes,
según los límites indicados arriba.

Se reprodujeron y corrigieron campos menores de 16 px, enlaces del encabezado
fuera del viewport al ampliar texto, foco sobre submenús cerrados y el botón
flotante sobre controles externos. WebKit detectó notificaciones de bucle de
`ResizeObserver`; las escrituras de disposición se trasladaron al siguiente
frame. La revisión independiente corrigió también la selección de idioma en
las pruebas: ahora se fija antes de navegar y se comprueba en ambas matrices.

La validación estática aprobó 11 páginas, 649 referencias locales y 33 objetos
de datos estructurados. La revisión de red completó 20 escenarios con fuentes
cargadas en todos ellos, sin desbordamientos, errores de página, solicitudes
fallidas ni respuestas HTTP de error. Se inspeccionaron capturas de portada,
equipo, contacto, eventos, membresía, auspicios, lectura y embeds.

Las verificaciones específicas de los tres motores confirmaron que el botón
flotante oculto tampoco intercepta pulsaciones sobre calendario, mapa o Spotify.
En Firefox, la comprobación de fotos sin JavaScript usa respuestas nativas de
imágenes: consultar propiedades en el mundo principal con JavaScript
desactivado bloquea la herramienta, no la descarga o presentación de las fotos.
