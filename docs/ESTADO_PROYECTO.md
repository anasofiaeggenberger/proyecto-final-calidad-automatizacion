# Estado del proyecto y pendientes

> **Estado de ejecución Jenkins:** los Builds #4, #5 y #6 utilizaron el commit
> `fdceef069d2a2c33894f0982d1dde38b90330e1f`. El commit de entrega es posterior e incorpora
> correcciones documentales e infraestructura; esta página conserva la separación entre ambos.
> Los defectos de eliminación HTML por nombre están corregidos y los límites de las ejecuciones
> Jenkins se documentan en `EVIDENCIA.md`.

Revisión histórica del 9 de noviembre de 2026, tras `git fetch origin`. Se compararon los archivos
e historiales de las ramas remotas; esa revisión no modificó `main` ni abrió un PR.

| Rama remota | SHA revisado | Aporte y estado en esta rama |
|---|---|---|
| main | 4dde2eb | SHA de la revisión histórica; posteriormente avanzó hasta `299c7b3` |
| docs/test-strategy | e74c9f3 | Plan técnico y guía, ya presentes en la base |
| docs/final-team-alignment | 8852924 | Contrato API y reparto, ya presentes en la base |
| docs/final-consistency-review | 9e7d9ac | Revisión documental, ya presente en la base |
| feat/base-hospital | e9bdfac | Migración hospitalaria, ya presente en la base |
| feat/hospital-ui-cleanup | 0567d04 | Dashboard y testids, ya presentes en la base |
| feat/sofi-domain-unit | 7ca9e09 | Dominio, 59 unitarias y gate, ya integrado en main |
| feat/juan-api-integration | d07d642 | API, 71 integración, Docker, ambientes, health gate; integrado conservando sus commits |
| feat/victor-e2e-playwright | d682281 al comenzar | Rama histórica; la implementación integrada se revisa en `main` |

## Pendientes detectados y resueltos

- Suite Playwright y POM: 17 casos por navegador, con smoke y regresión en Chromium y Firefox.
- Gate E2E conectado después de integración, con elección de navegador y reportes.
- Lint previo al build, tracking de etapa fallida y timeout.
- Código SMTP con credenciales inyectadas; las pruebas no equivalen a un envío real.
- Fallas reversibles documentadas para ensayos locales; la secuencia Jenkins verde → roja → verde
  sigue sin acreditarse.
- Documentación operativa, justificación SOLID, matriz E2E y matriz de integración trazable.

Se conservaron las responsabilidades de dominio/API/Docker y el historial de sus autores.
La rama se basó en main y se incorporó la rama de Juan como dependencia para no duplicar
su trabajo. La aplicación de negocio y el contrato API no cambian por las pruebas E2E.

## Pendientes del cierre conjunto

- La receta versionada de agente Jenkins (`infra/jenkins/`) todavía requiere un build limpio y
  una validación operativa separada; los Builds #4, #5 y #6 pertenecen a la instancia temporal.
- Configurar SMTP con credenciales autorizadas y acreditar recepción real del correo.
- Completar la evidencia de Jenkins verde/rojo/verde intencional y timeout; no se afirma que ya
  haya ocurrido.
- Identificar el commit de entrega mediante un tag público y un archivo MIU con URL, tag y SHA.

La instancia temporal ejecutó los Builds #4, #5 y #6 sobre el commit de ejecución
`fdceef069d2a2c33894f0982d1dde38b90330e1f`; ese SHA no es necesariamente el commit de entrega.
Esto no equivale a un build Jenkins limpio desde la receta versionada ni a un correo recibido.

## Actualización de auditoría PR #8

Ver [informe de auditoría](AUDITORIA_PR8.md).
La evidencia anterior conserva sus SHAs y conteos históricos. La validación local posterior a la
corrección por ID registró 72 unitarias, 71 de integración y 17 E2E por navegador; los manifiestos
Playwright disponibles identifican el checkout `46c4662`, anterior al commit actual `299c7b3`.
La cobertura 99.12 % y las 22 pruebas de notificaciones corresponden a artefactos históricos, no a
una medición nueva del `HEAD` actual.
La validación local histórica no acreditaba el aislamiento entre jobs: `disableConcurrentBuilds`
sólo protege el mismo job y esa prueba no usaba todavía la receta Jenkins aislada. La nueva
configuración declarativa usa un contenedor, puerto y volumen propios, pero su ejecución desde
cero sigue pendiente de evidencia. Un Jenkins limpio desde cero, SMTP recibido y la secuencia
verde → roja → verde siguen pendientes de evidencia.
