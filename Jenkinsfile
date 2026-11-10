pipeline {
    agent any

    parameters {
        choice(
            name: 'ENVIRONMENT',
            choices: ['ci', 'staging'],
            description: 'Ambiente donde se despliega y se prueba el artefacto.'
        )
        choice(
            name: 'SUITE',
            choices: ['smoke', 'regression'],
            description: 'smoke ejecuta sólo los casos marcados; regression ejecuta la suite completa.'
        )
    }

    options {
        skipDefaultCheckout(true)
        timestamps()
        timeout(time: 30, unit: 'MINUTES')
    }

    environment {
        PYTHON_BIN = '.venv/bin/python'
        UNIT_REPORT_DIR = 'reports/unit'
        COVERAGE_THRESHOLD = '90'
        INTEGRATION_REPORT_DIR = 'reports/integration'
        BUILD_REPORT_DIR = 'reports/build'
        IMAGE_NAME = 'hospital-queue'
        CI_PORT = '8001'
        STAGING_PORT = '8002'
    }

    stages {
        stage('Checkout') {
            steps {
                deleteDir()
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    set -eu
                    command -v uv
                    uv --version
                    uv venv --python 3.12 .venv
                    test -f requirements-ci.txt
                    uv pip sync --python "$PYTHON_BIN" requirements-ci.txt
                    "$PYTHON_BIN" --version
                    "$PYTHON_BIN" -m pytest --version
                '''
            }
        }

        stage('Unit Tests + Coverage') {
            steps {
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

        stage('Build Artifact') {
            steps {
                script {
                    env.COMMIT_SHA = sh(
                        script: 'git rev-parse HEAD',
                        returnStdout: true
                    ).trim()
                    env.APP_PORT = params.ENVIRONMENT == 'staging' ? env.STAGING_PORT : env.CI_PORT
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
                // --no-build garantiza que se despliega la imagen ya construida, no una nueva
                sh '''
                    set -eu
                    mkdir -p "$BUILD_REPORT_DIR"
                    export APP_VERSION="$COMMIT_SHA"
                    docker compose --profile "$ENVIRONMENT" down -v --remove-orphans
                    docker compose --profile "$ENVIRONMENT" up -d --no-build
                    docker compose --profile "$ENVIRONMENT" ps
                '''
            }
        }

        stage('Health Gate') {
            steps {
                // si la instancia no reporta el ambiente y el SHA desplegados, no se prueba nada más
                sh '''
                    set -eu
                    mkdir -p "$BUILD_REPORT_DIR"
                    REPORTE="$BUILD_REPORT_DIR/health-$ENVIRONMENT.txt"
                    # sin tuberia: con `| tee` el stage heredaba el codigo de tee (0) y
                    # un health invalido no detenia el pipeline
                    set +e
                    "$PYTHON_BIN" scripts/verificar_health.py \\
                        --url "http://127.0.0.1:$APP_PORT/api/health" \\
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
                sh '''
                    set -eu
                    mkdir -p "$INTEGRATION_REPORT_DIR"
                    if [ "$SUITE" = "smoke" ]; then
                        MARCADORES="-m smoke"
                    else
                        MARCADORES=""
                    fi
                    API_BASE_URL="http://127.0.0.1:$APP_PORT" \\
                    EXPECTED_AMBIENTE="$ENVIRONMENT" \\
                    EXPECTED_VERSION="$COMMIT_SHA" \\
                    "$PYTHON_BIN" -m pytest tests/integration -v $MARCADORES \\
                        --junitxml="$INTEGRATION_REPORT_DIR/junit.xml"
                '''
            }
        }
    }

    post {
        always {
            // los contenedores se apagan siempre, también ante fallo o timeout
            sh '''
                set +e
                mkdir -p reports/build
                docker compose --profile ci --profile staging logs --no-color --tail 200 \\
                    > "reports/build/compose-logs.txt" 2>&1
                docker compose --profile ci --profile staging down -v --remove-orphans
                exit 0
            '''
            script {
                def junitReport = 'reports/unit/junit.xml'
                def coverageReport = 'reports/unit/coverage.xml'
                def integrationReport = 'reports/integration/junit.xml'
                def buildReports = 'reports/build/*.txt'
                def reports = [junitReport, coverageReport, integrationReport].findAll {
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
            }
        }
    }
}
