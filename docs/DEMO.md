# Demo del proyecto (15 minutos y 5 de preguntas)

## Preparación

Partir del commit/tag entregado y de un build verde. El Jenkins necesita los plugins Pipeline,
Git, JUnit, Credentials Binding y HTML Publisher, un agente con Python 3, uv, Docker/Compose y
los requisitos del navegador. Ver [Jenkins y SMTP](JENKINS.md). No existe evidencia de correo
recibido hasta configurar SMTP y comprobar el buzón real.

Usar datos ficticios y un job exclusivo: los casos de integración y E2E vacían la cola de la
instancia seleccionada por HTTP. No ejecutar en una instancia de uso compartido.

## Guion

| Minutos | Acción y evidencia |
|---|---|
| 0–2 | Mostrar dashboard, registro, prioridad/FIFO y eliminación; repositorio, SHA y tag entregados |
| 2–4 | Mostrar las etapas, los cuatro parámetros y el build verde previo con cobertura |
| 4–6 | Ejecutar ci/regression/chromium y mostrar health con ambiente/SHA, JUnit y HTML |
| 6–8 | Ejecutar staging/smoke/firefox y mostrar otra instancia con la misma imagen y cola aislada |
| 8–11 | Aplicar la falla solicitada, revisar diff, hacer commit en demo y lanzar el build manual |
| 11–13 | Mostrar gate rojo, etapas siguientes omitidas, trace/captura si es E2E y correo en el buzón |
| 13–15 | Revertir la falla, hacer commit, volver a verde y explicar SRP/ISP y las técnicas ISTQB |

Tener builds verdes previos y las descargas de navegadores resueltas evita consumir la demo
esperando instalaciones. El commit de ruptura y el build automático de su push no sustituyen
el build manual que exige la consigna.

## Fallas reversibles por capa

Crear una rama temporal desde el commit entregado:

```bash
git switch -c demo/gates
.venv/bin/python scripts/preparar_demo.py apply e2e
git diff
git add templates/index.html
git commit -m "Demostrar falla de interfaz"
git push -u origin demo/gates
```

El job de demo debe apuntar a esa rama. Para integración o unitarias, sustituir e2e por
integration o unit y agregar únicamente el archivo indicado en la tabla.

| Capa | Cambio real en aplicación | Gate esperado |
|---|---|---|
| unit | Invierte la prioridad en Patient.sort_key | Unit Tests + Coverage, antes de construir |
| integration | Alta JSON responde 200 en vez de 201 | Integration Tests, antes de E2E |
| e2e | Cambia el testid del botón de registro | E2E Tests; unitarias y API conservan su comportamiento |

Restaurar sólo el parche aplicado, sin borrar otros cambios:

```bash
.venv/bin/python scripts/preparar_demo.py revert e2e
git diff
git add templates/index.html
git commit -m "Restaurar interfaz de registro"
git push
```

El asistente valida la rama y el parche antes de modificar archivos. Si el cambio de ruptura
ya se había confirmado, revert lo devuelve al contenido sano y deja ese arreglo listo para
un nuevo commit. No se desactiva ni modifica ninguna prueba.

## Evidencia para completar en Jenkins

Guardar número/enlace del build, SHA completo, ambiente, suite/navegador, etapa/caso fallido,
JUnit/cobertura, health, screenshot/trace y captura del correo recibido. Registrar
verde → rojo → verde por cada capa en EVIDENCIA.md. Para un timeout, documentar también el
build abortado y el correo: unsuccessful cubre el aborto. Los ensayos locales se identifican
como locales; no se presentan como builds Jenkins.
