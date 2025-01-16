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
                sh '''
                # Poetry 설치 확인 및 설치
                if ! command -v poetry &> /dev/null; then
                    echo "Poetry가 설치되어 있지 않습니다. 설치를 진행합니다."
                    curl -sSL https://install.python-poetry.org | python3 -
                    export PATH="$HOME/.local/bin:$PATH"
                else
                    echo "Poetry가 이미 설치되어 있습니다."
                fi

                # Poetry 버전 확인
                poetry --version
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                sh '''
                # 가상 환경 생성 및 의존성 설치
                poetry install --no-interaction --no-ansi
                '''
            }
        }

        stage('Run Tests') {
            steps {
                sh '''
                # Poetry 가상 환경에서 테스트 실행
                poetry run pytest
                '''
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
