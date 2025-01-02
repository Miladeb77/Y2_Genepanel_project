pipeline {
    agent any
    environment {
        IMAGE_NAME = "genepanel-app" // Name of the Docker image
        CONTAINER_NAME = "genepanel-container" // Name of the Docker container
        TEST_RESULTS_DIR = "output/test-results" // Directory for test results
        TEST_DIR = "tests" // Directory containing tests
    }
    stages {
        stage("Checkout Code") {
            steps {
                echo "Checking out the source code from GitHub..."
                git branch: 'development', url: 'https://github.com/Miladeb77/Y2_Genepanel_project.git'
            }
        }
        stage("Build Docker Image") {
            steps {
                script {
                    echo "Building the Docker image..."
                    bat """
                        docker build -t %IMAGE_NAME% .
                    """
                }
            }
        }
        stage("Run Unit Tests in Docker Container") {
            steps {
                script {
                    echo "Running tests in the Docker container..."
                    bat """
                        docker run --rm --name %CONTAINER_NAME% ^
                        -v %WORKSPACE%\\%TEST_RESULTS_DIR%:/app/output ^
                        %IMAGE_NAME% pytest /app/%TEST_DIR% --junitxml=/app/output/test-results.xml
                    """
                }
            }
        }
        stage("Archive Test Results") {
            steps {
                echo "Archiving test results..."
                junit "**/${TEST_RESULTS_DIR}/test-results.xml"
            }
        }
        stage("Lint and Static Code Analysis") {
            steps {
                script {
                    echo "Running flake8 for linting..."
                    bat """
                        docker run --rm --name %CONTAINER_NAME% ^
                        %IMAGE_NAME% flake8 PanelGeneMapper/ > lint-results.txt || true
                    """
                }
                archiveArtifacts artifacts: "lint-results.txt", allowEmptyArchive: true
            }
        }
        stage("Generate Documentation") {
            steps {
                script {
                    echo "Generating documentation with pdoc..."
                    bat """
                        docker run --rm --name %CONTAINER_NAME% ^
                        %IMAGE_NAME% pdoc --html --output-dir /app/docs PanelGeneMapper/
                    """
                }
                archiveArtifacts artifacts: "/app/docs/**", allowEmptyArchive: true
            }
        }
    }
    post {
        always {
            script {
                echo "Cleaning up Docker resources..."
                bat """
                    docker system prune --all --volumes --force || true
                """
            }
        }
        success {
            echo "Pipeline executed successfully!"
        }
        failure {
            echo "Pipeline failed. Check logs for details."
        }
    }
}
