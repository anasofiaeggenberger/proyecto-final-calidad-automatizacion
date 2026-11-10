# Revisión de ramas y pendientes

Revisión del 9 de noviembre de 2026, tras git fetch origin. Se compararon los archivos e
historiales de todas las ramas remotas; no se modificó main ni se abrió un PR.

| Rama remota | SHA revisado | Aporte y estado en esta rama |
|---|---|---|
| main | 4dde2eb | PR #7 de Juan integrado; base actual de la auditoría |
| docs/test-strategy | e74c9f3 | Plan técnico y guía, ya presentes en la base |
| docs/final-team-alignment | 8852924 | Contrato API y reparto, ya presentes en la base |
| docs/final-consistency-review | 9e7d9ac | Revisión documental, ya presente en la base |
| feat/base-hospital | e9bdfac | Migración hospitalaria, ya presente en la base |
| feat/hospital-ui-cleanup | 0567d04 | Dashboard y testids, ya presentes en la base |
| feat/sofi-domain-unit | 7ca9e09 | Dominio, 59 unitarias y gate, ya integrado en main |
| feat/juan-api-integration | d07d642 | API, 71 integración, Docker, ambientes, health gate; integrado conservando sus commits |
| feat/victor-e2e-playwright | d682281 al comenzar | No tenía implementación propia; ahora incluye POM/E2E, gate, SMTP y demo |

## Pendientes detectados y resueltos

- Suite Playwright y POM con estado aislado: 17 casos, smoke y regresión, Chromium y Firefox.
- Gate E2E conectado después de integración, elección de navegador y reportes.
- Lint previo al build, tracking de etapa fallida y timeout.
- Código SMTP por credenciales inyectadas y 22 pruebas sin envío real.
- Fallas reales y reversibles para las tres capas, con guion y evidencia local.
- Documentación operativa, justificación SOLID, matriz E2E y evidencia ordenada.

Se conservaron las responsabilidades de dominio/API/Docker y el historial de sus autores.
La rama se basó en main y se incorporó la rama de Juan como dependencia para no duplicar
su trabajo. La aplicación de negocio y el contrato API no cambian por las pruebas E2E.

## Pendientes del cierre conjunto

- Configurar el job/agente Jenkins y SMTP, ejecutar builds y acreditar correo recibido.
- Completar las evidencias de Jenkins verde/rojo/verde, timeout y ambos ambientes.
- Ana debe completar su justificación documental de cobertura en DECISIONES.md.
- Coordinar si la UI debe eliminar homónimos por ID; actualmente elimina por nombre.
- Elegir el tag final y el commit integrado del equipo, y entregar archivo MIU con URL/tag/SHA.

El código de infraestructura existe y fue comprobado por componentes localmente;
eso no equivale a un build Jenkins ni a un correo recibido.

## Actualización de auditoría PR #8

Ver [informe de auditoría](AUDITORIA_PR8.md).
La evidencia anterior conserva sus SHAs y conteos históricos. La auditoría actual registra
22 pruebas SMTP, cobertura 99.12 % y smoke/regression en ambos navegadores.
No se considera validado el aislamiento entre jobs: disableConcurrentBuilds sólo protege
el mismo job; Compose y su cleanup comparten nombres y puertos. La solución compartida
requiere aprobación. Dominio concurrente, Jenkins real y SMTP recibido siguen pendientes.
