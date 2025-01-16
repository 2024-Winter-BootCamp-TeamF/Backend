pipeline {
    agent any

    environment {
        REPOSITORY = "jeonjong/teamf-backend" // Docker Hub ID와 레포지토리 이름
        DOCKERHUB_CREDENTIALS = credentials('team-f-docker-hub') // Jenkins에 등록된 Docker Hub id
        IMAGE_TAG = "" // Docker 이미지 태그
    }

    stages {
        stage('Checkout Code') {
            steps {
                cleanWs()
                git branch: 'main', url: 'https://github.com/2024-Winter-BootCamp-TeamF/Backend.git'
            }
        }

        stage('Setup Python Environment') {
            steps {
                sh '''
                if ! command -v poetry &> /dev/null; then
                    echo "Poetry가 설치되어 있지 않습니다. 설치를 진행합니다."
                    curl -sSL https://install.python-poetry.org | python3 -
                    export PATH="$HOME/.local/bin:$PATH"
                fi
                poetry --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                poetry install --no-interaction --no-ansi
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                poetry run pytest
                '''
            }
        }

        stage('Set Image Tag') {
            steps {
                script {
                    IMAGE_TAG = "v1.0.${BUILD_NUMBER}"
                    echo "Docker image tag set to: ${IMAGE_TAG}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                sh "docker build -t ${REPOSITORY}:${IMAGE_TAG} ."
            }
        }

        stage('Push Docker Image') {
            steps {
                sh '''
                echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin
                docker push ${REPOSITORY}:${IMAGE_TAG}
                '''
            }
        }

        stage('Clean Up') {
            steps {
                sh '''
                docker rmi ${REPOSITORY}:${IMAGE_TAG} || true
                docker image prune -f
                '''
            }
        }
    }

    post {
        success {
            echo "Pipeline completed successfully!"
        }
        failure {
            echo "Pipeline failed. Check the logs for details."
        }
        always {
            cleanWs()
        }
    }
}
