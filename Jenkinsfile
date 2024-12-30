pipeline {
    agent {
        docker {
            image "docker:24.0.6-git" // Docker image for Jenkins agent
        }
    }
    environment {
        CONTAINER_SUFFIX = "${BUILD_NUMBER}" // Use the build number as a unique container suffix
        DOCKER_NETWORK = "genepanel_network-$CONTAINER_SUFFIX" // Unique Docker network for this build
        DATA_VOLUME = "genepanel_shared_space" // Shared data volume
    }
    stages {
        stage("Prepare Environment") {
            steps {
                script {
                    // Clean up dangling Docker components and create Docker network
                    sh 'docker system prune --all --volumes --force || true'
                    sh 'docker network create $DOCKER_NETWORK'
                }
            }
        }
        stage("Checkout Code") {
            steps {
                checkout scm // Checkout the source code
            }
        }
        stage("Build and Run Application Container") {
            steps {
                script {
                    def dockerfile = './Dockerfile' // Path to the Dockerfile
                    def appContainer = docker.build("genepanel_app-${CONTAINER_SUFFIX}", "--no-cache -f ${dockerfile} .")
                    // Run the main application container
                    appContainer.run("-d --name genepanel_app --network $DOCKER_NETWORK -v $DATA_VOLUME:/app/output")
                }
            }
        }
        stage("Run Pytest") {
            steps {
                script {
                    def testsSuccessful = false

                    // Retry logic for database connections and running tests
                    for (int attempt = 1; attempt <= 5; attempt++) {
                        echo "Attempt $attempt to connect and run tests..."
                        def exitCode = sh(script: '''
                            docker exec genepanel_app pytest --junitxml=/app/output/test-results.xml
                        ''', returnStatus: true)

                        if (exitCode == 0) {
                            testsSuccessful = true
                            echo "Tests executed successfully!"
                            break
                        }

                        echo "Connection failed or tests unsuccessful. Retrying in 30 seconds..."
                        sleep 30
                    }

                    if (!testsSuccessful) {
                        error("All attempts to run tests failed.")
                    }
                }
            }
        }
        stage("Archive Test Results") {
            steps {
                // Archive test results
                junit '/app/output/test-results.xml'
            }
        }
    }
    post {
        always {
            script {
                // Clean up Docker resources
                sh 'docker stop genepanel_app || true'
                sh 'docker rm genepanel_app || true'
                sh 'docker network rm $DOCKER_NETWORK || true'
                sh 'docker system prune --all --volumes --force || true'
            }
        }
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed. Check logs for more details."
        }
    }
}
