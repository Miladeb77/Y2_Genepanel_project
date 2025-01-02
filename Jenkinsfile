pipeline {
    agent any
    environment {
        IMAGE_NAME = "genepanel-app" // Name for the Docker image
        CONTAINER_NAME = "genepanel-container" // Name for the Docker container
        TEST_RESULTS_DIR = "output/test-results" // Directory for test results
    }
    stages {
        stage("Checkout Code") {
            steps {
                echo "Checking out the source code from GitHub..."
                checkout scm
            }
        }
        stage("Build Docker Image") {
            steps {
                script {
                    echo "Building the Docker image..."
                    sh """
                        docker build -t $IMAGE_NAME .
                    """
                }
            }
        }
        stage("Run Unit Tests in Docker Container") {
            steps {
                script {
                    echo "Running tests in the Docker container..."
                    sh """
                        docker run --rm --name $CONTAINER_NAME \
                            -v \$(pwd)/$TEST_RESULTS_DIR:/app/output \
                            $IMAGE_NAME pytest --junitxml=/app/output/test-results.xml
                    """
                }
            }
        }
        stage("Archive Test Results") {
            steps {
                echo "Archiving test results..."
                junit "$TEST_RESULTS_DIR/test-results.xml"
            }
        }
        stage("Lint and Static Code Analysis") {
            steps {
                script {
                    echo "Running flake8 for linting..."
                    sh """
                        docker run --rm --name $CONTAINER_NAME \
                            $IMAGE_NAME flake8 PanelGeneMapper/ > lint-results.txt || true
                    """
                }
                archiveArtifacts artifacts: "lint-results.txt", allowEmptyArchive: true
            }
        }
        stage("Generate Documentation") {
            steps {
                script {
                    echo "Generating documentation with pdoc..."
                    sh """
                        docker run --rm --name $CONTAINER_NAME \
                            $IMAGE_NAME pdoc --html --output-dir /app/docs PanelGeneMapper/
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
                sh """
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
