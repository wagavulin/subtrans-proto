
```
sudo docker run -p 8080:8080 -p 50000:50000 --network jenkins jenkins/jenkins:lts-jdk21

sudo docker run --name jenkins-controller -p 8080:8080 -p 50000:50000 --network jenkins -v `pwd`/jenkins_home:/var/jenkins_home  jenkins/jenkins:lts-jdk21

sudo docker run -u root --name agent1 --network jenkins --init my-jenkins-agent -url http://172.18.0.2:8080 -workDir /var/jenkins 768866f00d3adc8f0e5d593152ab76b26f054d8d556d08edf1e8dab7f211466a agent1
```

```groovy
pipeline {
    agent any

    stages {
        stage('Clone pytest') {
            steps {
                git(
                    url: "https://github.com/wagavulin/pytest.git",
                    branch: "main"
                )
            }
        }
        stage('Hello') {
            steps {
                echo 'Hello World'
            }
        }
        stage('Run python') {
            steps {
                sh '''#!/bin/bash
                    python ./pytest1.py
                '''
                archiveArtifacts artifacts: 'out.png'
            }
        }
    }
}
```
