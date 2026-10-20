# RUMi — backend gratis (Cloudflare Worker)

RUMi funciona **sin este Worker**: con `rumiEndpoint` vacío en `assets/config.js` contesta
con la base de conocimiento (`assets/rumi/kb.json`) y, para preguntas abiertas, una cadena de
modelos gratis **sin key** llamada desde el navegador de cada visitante (`FREE_MODELS` en
`assets/rumi.js`): solo **OVHcloud AI Endpoints** (Mistral-Small → Mistral-Nemo → Llama 3.3 →
Qwen → gpt-oss), cuyo acceso anónimo está documentado oficialmente (2 req/min por IP y modelo;
servidores en Francia; "no se guardan ni comparten datos"). Revisado el 2026-10-18 y descartado:
LLM7 (sus términos exigen token y prohíben producción e integrarlo para terceros) y Pollinations
(acceso anónimo "legacy"). El Worker añade **Groq** (cuenta gratis) y **Cloudflare Workers AI**, y es más rápido y estable
para la competencia. Costo: **$0** (todos los servicios en plan gratis, sin tarjeta).

```
Sitio (GitHub Pages) ── RUMi widget (assets/rumi.js)
        │  herramientas locales: auditoría web (Microlink + PageSpeed), empleos (Jobicy),
        │  paletas, nombres (Datamuse), QR (api.qrserver.com), validación de email (Disify)
        └── POST /chat ──► Cloudflare Worker (este folder)
                              ├─ 1. Groq        (openai/gpt-oss-120b, razonamiento bajo)
                              ├─ 2. Workers AI  (Gemma 4 26B, sin key)
                              ├─ 3. OVHcloud    (Mistral Small, acceso anónimo documentado)
                              └─ si todo falla → el widget contesta localmente
```

## Instalar (una vez, ~20 minutos)

1. **Cuentas gratis** (usar el correo del capítulo, no uno personal):
   - Cloudflare: https://dash.cloudflare.com/sign-up (plan Free)
   - Groq: https://console.groq.com → API Keys → Create
2. **Desplegar** (requiere Node.js) desde esta carpeta:
   ```bash
   cd worker
   npx wrangler login
   npx wrangler secret put GROQ_API_KEY      # pegar la key de Groq
   npx wrangler secret put ADMIN_KEY         # inventar una clave larga (para /unanswered)
   npx wrangler deploy
   ```
   Al final imprime la URL, p. ej. `https://rumi.<cuenta>.workers.dev`.
3. **Conectar el sitio**: poner esa URL en `rumiEndpoint` de `assets/config.js`, commit y push.
4. **Probar**: `https://rumi.<cuenta>.workers.dev/health` debe listar `groq`, `workers-ai`, `ovh`.

### Opcional: registro de preguntas sin respuesta
```bash
npx wrangler kv namespace create RUMI_LOG   # copiar el id en wrangler.toml y descomentar el bloque
npx wrangler deploy
```
Ver la lista: `https://rumi.<cuenta>.workers.dev/unanswered?key=<ADMIN_KEY>`. Sirve para el
Monthly Insights Report: lo que la gente pregunta y el sitio no contesta es contenido por crear.

## Mantener al día
- Al editar páginas: `python scripts/build_rumi_kb.py` y hacer commit de `assets/rumi/kb.json`.
  El Worker lee ese archivo del sitio publicado (caché de 1 hora).
- Datos del Chapter Plan y su calendario tentativo: `scripts/rumi_plan.json` (sin presupuesto).
- Preguntas frecuentes curadas: `scripts/rumi_faq.json` (palabras clave + respuesta EN/ES). El widget
  las contesta directo y el Worker se las pasa a la IA como respuestas aprobadas.
- Si un proveedor retira un modelo, cambiar `GROQ_MODEL` o `WORKERS_AI_MODEL` en `wrangler.toml`.
- Capacidad de Groq: el límite real son los tokens (8,000/min y 200,000/día por organización), no
  los 1,000 pedidos/día. Con ~3,000 tokens por pregunta son ~2-3 respuestas de IA por minuto y
  ~60 al día; la mayoría de preguntas las contesta el FAQ local sin gastar cuota.
- Descartados a propósito (revisión de términos 2026-10-18): NVIDIA Build, Kilo `:free`, Gemini
  free, OpenRouter free, LLM7, Pollinations. Ver el comentario en `providers()`.

## Privacidad y seguridad
- Emails y teléfonos que escribe el visitante se borran (`[email]`, `[phone]`) antes de enviarlos
  a cualquier IA.
- Los leads (auspicios, clientes de ELEVATE) nunca pasan por la IA: van a `formEndpoint`
  o a un borrador de correo a ama@uprm.edu.
- Solo acepta peticiones desde amauprm.org (y localhost); 20 mensajes/minuto por IP.
- Ninguna key vive en el repo: todas son `wrangler secret`.

## Métricas (GA4)
`rumi_open`, `rumi_message` (mode `ai`/`local`/`search`, intent), `rumi_cta_click`, `rumi_tool`
(audit, palette, qr, jobs, naming, bio), `rumi_lead` (sponsor/elevate),
`rumi_unanswered`, `rumi_feedback` (👍/👎 por intent), `rumi_persona` (student/business/sponsor/alum),
`rumi_teaser_shown` y `rumi_teaser_click`. Los clics a
membresía también envían `membership_interest_click` con `source: rumi`.
