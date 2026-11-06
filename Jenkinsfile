pipeline {
    agent any

    options {
        skipDefaultCheckout(true)
        timestamps()
    }

    environment {
        PYTHON_BIN = '.venv/bin/python'
        UNIT_REPORT_DIR = 'reports/unit'
        COVERAGE_THRESHOLD = '90'
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
    }

    post {
        always {
            script {
                def junitReport = 'reports/unit/junit.xml'
                def coverageReport = 'reports/unit/coverage.xml'
                def reports = [junitReport, coverageReport].findAll { fileExists(it) }

                if (fileExists(junitReport)) {
                    junit testResults: junitReport, allowEmptyResults: false
                } else {
                    echo 'JUnit XML no generado; se omite su publicación.'
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
            }
        }
    }
}
