pipeline {
    agent any

    parameters {
        string(
            name: 'NOTIFY_EMAILS',
            defaultValue: 'victorsaravia@ufm.edu',
            description: 'Destinatarios autorizados del correo de fallo, separados por coma.'
        )
        choice(
            name: 'ENVIRONMENT',
            choices: ['ci', 'staging'],
            description: 'Ambiente donde se despliega y se prueba el artefacto.'
        )
        choice(
            name: 'BROWSER',
            choices: ['chromium', 'firefox'],
            description: 'Navegador que ejecuta los recorridos E2E.'
        )
        choice(
            name: 'SUITE',
            choices: ['regression', 'smoke'],
            description: 'smoke ejecuta sólo los casos marcados; regression ejecuta la suite completa.'
        )
    }

    triggers {
        pollSCM('H/2 * * * *')
    }

    options {
        skipDefaultCheckout(true)
        timestamps()
        disableConcurrentBuilds()
        skipStagesAfterUnstable()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        FAILED_STAGE = 'Checkout'
        E2E_REPORT_DIR = 'reports/e2e'
        PYTHON_BIN = '.venv/bin/python'
        UNIT_REPORT_DIR = 'reports/unit'
        COVERAGE_THRESHOLD = '90'
        INTEGRATION_REPORT_DIR = 'reports/integration'
        BUILD_REPORT_DIR = 'reports/build'
        IMAGE_NAME = 'hospital-queue'
    }

    stages {
        stage('Checkout') {
            steps {
                script { env.FAILED_STAGE = 'Checkout' }
                deleteDir()
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                script { env.FAILED_STAGE = 'Setup Python' }
                sh '''
                    set -eu
                    command -v uv
                    uv --version
                    uv venv --python 3.12 .venv
                    test -f requirements-ci.txt
                    uv pip sync --python "$PYTHON_BIN" requirements-ci.txt
                    uv pip install --python "$PYTHON_BIN" --require-hashes -r requirements-e2e.txt
                    "$PYTHON_BIN" --version
                    "$PYTHON_BIN" -m pytest --version
                '''
            }
        }

        stage('Lint') {
            steps {
                script { env.FAILED_STAGE = 'Lint' }
                sh '"$PYTHON_BIN" -m ruff check app.py api domain services tests scripts'
            }
        }

        stage('Unit Tests + Coverage') {
            steps {
                script { env.FAILED_STAGE = 'Unit Tests + Coverage' }
                sh '''
                    set -eu
                    mkdir -p "$UNIT_REPORT_DIR"
                    "$PYTHON_BIN" -m pytest tests/unit -q \\
                        --junitxml="$UNIT_REPORT_DIR/junit.xml" \\
                        --cov=domain \\
                        --cov=services \\
                        --cov-report=term-missing \\
                        --cov-report=xml:"$UNIT_REPORT_DIR/coverage.xml" \\
                        --cov-fail-under="$COVERAGE_THRESHOLD"
                '''
            }
        }

        stage('Notification Tests') {
            steps {
                script { env.FAILED_STAGE = 'Notification Tests' }
                sh '"$PYTHON_BIN" -m pytest tests/notifications tests/pipeline -q --junitxml=reports/notifications/junit.xml'
            }
        }

        stage('Build Artifact') {
            steps {
                script { env.FAILED_STAGE = 'Build Artifact' }
                script {
                    env.COMMIT_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()
                    env.COMPOSE_PROJECT_NAME = sh(
                        script: '''"$PYTHON_BIN" -c 'import uuid; print("hospital-build-" + uuid.uuid4().hex)' ''',
                        returnStdout: true
                    ).trim()
                }
                // el artefacto se construye una sola vez por build y queda etiquetado con el SHA
                sh '''
                    set -eu
                    command -v docker
                    mkdir -p "$BUILD_REPORT_DIR"
                    docker build \\
                        --build-arg APP_VERSION="$COMMIT_SHA" \\
                        -t "$IMAGE_NAME:$COMMIT_SHA" .
                    {
                        echo "build=$BUILD_NUMBER"
                        echo "commit=$COMMIT_SHA"
                        echo "imagen=$IMAGE_NAME:$COMMIT_SHA"
                        echo "image_id=$(docker image inspect "$IMAGE_NAME:$COMMIT_SHA" --format '{{.Id}}')"
                        echo "ambiente=$ENVIRONMENT"
                        echo "suite=$SUITE"
                    } > "$BUILD_REPORT_DIR/artefacto.txt"
                    cat "$BUILD_REPORT_DIR/artefacto.txt"
                '''
            }
        }

        stage('Deploy') {
            steps {
                script { env.FAILED_STAGE = 'Deploy' }
                // --no-build garantiza que se despliega la imagen ya construida, no una nueva
                sh '''
                    set -eu
                    "$PYTHON_BIN" scripts/gestionar_ambiente.py deploy \\
                        --project "$COMPOSE_PROJECT_NAME" --environment "$ENVIRONMENT" \\
                        --version "$COMMIT_SHA" --report-dir "$BUILD_REPORT_DIR"
                '''
                script { env.APP_BASE_URL = readFile('reports/build/endpoint.txt').trim() }
            }
        }

        stage('Health Gate') {
            steps {
                script { env.FAILED_STAGE = 'Health Gate' }
                // si la instancia no reporta el ambiente y el SHA desplegados, no se prueba nada más
                sh '''
                    set -eu
                    mkdir -p "$BUILD_REPORT_DIR"
                    REPORTE="$BUILD_REPORT_DIR/health-$ENVIRONMENT.txt"
                    # sin tuberia: con `| tee` el stage heredaba el codigo de tee (0) y
                    # un health invalido no detenia el pipeline
                    set +e
                    "$PYTHON_BIN" scripts/verificar_health.py \\
                        --url "$APP_BASE_URL/api/health" \\
                        --ambiente "$ENVIRONMENT" \\
                        --version "$COMMIT_SHA" \\
                        --timeout 90 > "$REPORTE" 2>&1
                    CODIGO_HEALTH=$?
                    set -e
                    cat "$REPORTE"
                    exit "$CODIGO_HEALTH"
                '''
            }
        }

        stage('Integration Tests') {
            steps {
                script { env.FAILED_STAGE = 'Integration Tests' }
                sh '''
                    set -eu
                    mkdir -p "$INTEGRATION_REPORT_DIR"
                    if [ "$SUITE" = "smoke" ]; then
                        MARCADORES="-m smoke"
                    else
                        MARCADORES=""
                    fi
                    API_BASE_URL="$APP_BASE_URL" \\
                    EXPECTED_AMBIENTE="$ENVIRONMENT" \\
                    EXPECTED_VERSION="$COMMIT_SHA" \\
                    "$PYTHON_BIN" -m pytest tests/integration -v $MARCADORES \\
                        --junitxml="$INTEGRATION_REPORT_DIR/junit.xml"
                '''
            }
        }

        stage('E2E Tests') {
            options {
                timeout(time: 8, unit: 'MINUTES')
            }
            steps {
                script { env.FAILED_STAGE = 'E2E Tests' }
                sh '''
                    set -eu
                    "$PYTHON_BIN" -m playwright install "$BROWSER"
                    E2E_BASE_URL="$APP_BASE_URL" \\
                    E2E_ALLOW_CLEANUP=1 \\
                    EXPECTED_AMBIENTE="$ENVIRONMENT" \\
                    EXPECTED_VERSION="$COMMIT_SHA" \\
                    "$PYTHON_BIN" scripts/ejecutar_e2e.py \\
                        --suite "$SUITE" --browser "$BROWSER" \\
                        --report-dir "$E2E_REPORT_DIR"
                '''
            }
        }
    }

    post {
        unsuccessful {
            script {
                // También se ejecuta ante timeout/abort. No oculta el fallo original.
                try {
                    withCredentials([
                        file(credentialsId: 'smtp-config', variable: 'SMTP_CONFIG_FILE'),
                        usernamePassword(credentialsId: 'smtp-auth',
                            usernameVariable: 'SMTP_USERNAME', passwordVariable: 'SMTP_PASSWORD')
                    ]) {
                        sh '''
                            set +x
                            python3 scripts/notificar_fallo.py \\
                                --to "$NOTIFY_EMAILS" --build "$BUILD_NUMBER" \\
                                --commit "${COMMIT_SHA:-${GIT_COMMIT:-desconocido}}" \\
                                --environment "$ENVIRONMENT" --stage "$FAILED_STAGE" \\
                                --log-url "${BUILD_URL}console"
                        '''
                    }
                } catch (error) {
                    echo 'La notificación SMTP no pudo completarse; el build sigue fallido.'
                } finally {
                    archiveArtifacts artifacts: 'reports/notifications/**', allowEmptyArchive: true
                }
            }
        }
        always {
            script {
                def cleanupStatus = 0
                if (fileExists('reports/build/deployment.json')) {
                    if (currentBuild.currentResult == 'SUCCESS') {
                        env.FAILED_STAGE = 'Cleanup'
                    }
                    cleanupStatus = sh(
                        script: '"$PYTHON_BIN" scripts/gestionar_ambiente.py cleanup --report-dir "$BUILD_REPORT_DIR"',
                        returnStatus: true
                    )
                } else {
                    echo 'Sin despliegue propio; no se ejecuta Docker cleanup.'
                }
                def junitReport = 'reports/unit/junit.xml'
                def coverageReport = 'reports/unit/coverage.xml'
                def integrationReport = 'reports/integration/junit.xml'
                def notificationReport = 'reports/notifications/junit.xml'
                def e2eReport = 'reports/e2e/junit.xml'
                def buildReports = 'reports/build/**'
                def reports = [junitReport, coverageReport, integrationReport, e2eReport, notificationReport].findAll {
                    fileExists(it)
                }

                if (fileExists(junitReport)) {
                    junit testResults: junitReport, allowEmptyResults: false
                } else {
                    echo 'JUnit XML no generado; se omite su publicación.'
                }

                if (fileExists(integrationReport)) {
                    junit testResults: integrationReport, allowEmptyResults: false
                } else {
                    echo 'JUnit de integración no generado; se omite su publicación.'
                }

                if (fileExists(notificationReport)) {
                    junit testResults: notificationReport, allowEmptyResults: false
                }
                if (fileExists(e2eReport)) {
                    junit testResults: e2eReport, allowEmptyResults: false
                }
                archiveArtifacts(
                    artifacts: 'reports/e2e/**',
                    allowEmptyArchive: true,
                    fingerprint: true
                )
                if (fileExists('reports/e2e/report.html')) {
                    publishHTML(target: [
                        reportDir: 'reports/e2e', reportFiles: 'report.html',
                        reportName: 'E2E Playwright', keepAll: true,
                        alwaysLinkToLastBuild: true, allowMissing: false
                    ])
                }

                if (reports) {
                    archiveArtifacts(
                        artifacts: reports.join(','),
                        allowEmptyArchive: false,
                        fingerprint: true
                    )
                } else {
                    echo 'No se generaron reportes unitarios; se omite el archivado.'
                }

                archiveArtifacts(
                    artifacts: buildReports,
                    allowEmptyArchive: true,
                    fingerprint: true
                )
                if (cleanupStatus != 0) {
                    error('Falló el cleanup del build; no se borraron recursos sin propiedad comprobada.')
                }
            }
        }
    }
}
