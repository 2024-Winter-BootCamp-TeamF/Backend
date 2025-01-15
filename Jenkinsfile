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
                // 작업 디렉토리를 정리하고 GitHub에서 코드를 가져옵니다.
                cleanWs()
                git branch: 'main', url: 'https://github.com/2024-Winter-BootCamp-TeamF/Backend.git'
            }
        }

        stage('Setup Python Environment') {
            steps {
                script {
                    // Python 환경을 준비합니다.
                    sh 'python3 --version'
                    sh 'python3 -m venv venv'
                    sh '. venv/bin/activate && pip install --upgrade pip'
                }
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    // requirements.txt에 명시된 의존성을 설치합니다.
                    sh '. venv/bin/activate && pip install -r requirements.txt'
                }
            }
        }

        stage('Run Tests') {
            steps {
                script {
                    // 테스트를 실행합니다. (예: pytest)
                    sh '. venv/bin/activate && pytest'
                }
            }
        }

        stage('Set Image Tag') {
            steps {
                script {
                    // 브랜치 이름에 따라 Docker 이미지 태그를 설정합니다.
                    IMAGE_TAG = "v1.0.${BUILD_NUMBER}"
                    echo "Docker image tag set to: ${IMAGE_TAG}"
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    // Docker 이미지를 빌드합니다.
                    sh "docker build -t ${REPOSITORY}:${IMAGE_TAG} ."
                }
            }
        }

        stage('Push Docker Image') {
            steps {
                script {
                    // Docker Hub에 로그인하고 이미지를 푸시합니다.
                    sh "echo ${DOCKERHUB_CREDENTIALS_PSW} | docker login -u ${DOCKERHUB_CREDENTIALS_USR} --password-stdin"
                    sh "docker push ${REPOSITORY}:${IMAGE_TAG}"
                }
            }
        }

        stage('Clean Up') {
            steps {
                script {
                    // 로컬에서 빌드한 Docker 이미지를 삭제하여 공간을 확보합니다.
                    sh "docker rmi ${REPOSITORY}:${IMAGE_TAG}"
                }
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
            // Jenkins 작업 디렉토리를 정리합니다.
            cleanWs()
        }
    }
}
