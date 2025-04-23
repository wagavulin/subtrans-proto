
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

```Dockerfile
FROM jenkins/inbound-agent:latest

USER root
SHELL ["/bin/bash", "-c"]
RUN apt-get update

## pyenv
#RUN apt-get install -y build-essential libssl-dev zlib1g-dev libbz2-dev libreadline-dev libsqlite3-dev curl libncursesw5-dev xz-utils tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
#RUN git clone https://github.com/pyenv/pyenv.git ~/.pyenv
#RUN echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
#RUN echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
#RUN echo 'eval "$(pyenv init -)"' >> ~/.bashrc
#RUN source ~/.bashrc && pyenv install 3.13.3

## Miniconda
RUN apt-get install -y wget
RUN wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh && \
    sh Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3 && \
    rm -r Miniconda3-latest-Linux-x86_64.sh
ENV PATH=/opt/miniconda3/bin:$PATH
RUN conda create -n py313 python=3.13 -y
RUN conda init
RUN echo ". /opt/miniconda3/etc/profile.d/conda.sh" >> ~/.bashrc && echo "conda activate py313" >> ~/.bashrc
SHELL ["/bin/bash", "-c"]
RUN pip install matplotlib seaborn
```
