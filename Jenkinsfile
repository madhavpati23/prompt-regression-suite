// Jenkins declarative pipeline — same gates as the GitHub Actions workflow.
// Runs unit tests, then the regression gate against the checked-in mock baseline
// (exit 2 on a regression fails the build), and archives the HTML/JSON report
// so stakeholders can open it from the build page.
pipeline {
    agent any
    options { timestamps() }

    stages {
        stage('Setup') {
            steps {
                sh '''
                    python -m venv .venv
                    . .venv/bin/activate
                    pip install --upgrade pip
                    pip install -e ".[dev]"
                '''
            }
        }
        stage('Unit tests') {
            steps {
                sh '. .venv/bin/activate && pytest -q'
            }
        }
        stage('Regression gate + report') {
            steps {
                // exits 2 if the suite regresses vs the baseline -> fails the build
                sh '''
                    . .venv/bin/activate
                    python -m prompt_regression run \
                        --baseline baselines/mock.baseline.json \
                        --html report.html --json report.json
                '''
            }
        }
    }

    post {
        always {
            archiveArtifacts artifacts: 'report.html,report.json', allowEmptyArchive: true
        }
    }
}
