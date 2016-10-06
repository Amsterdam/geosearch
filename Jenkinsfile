#!groovy

def tryStep(String message, Closure block, Closure tearDown = null) {
    try {
        block();
    }
    catch (Throwable t) {
        slackSend message: "${env.JOB_NAME}: ${message} failure ${env.BUILD_URL}", channel: '#ci-channel', color: 'danger'

        throw t;
    }
    finally {
        if (tearDown) {
            tearDown();
        }
    }
}


node {

    stage("Checkout") {
        checkout scm
    }

    stage('Test') {
        tryStep "Test", {
            sh "docker-compose -p geosearch -f .jenkins/docker-compose.yml build"
            sh "docker-compose -p geosearch -f .jenkins/docker-compose.yml up -d atlas_db"
            sh "docker-compose -p geosearch -f .jenkins/docker-compose.yml exec atlas_db /bin/update-atlas.sh"
            sh "docker-compose -p geosearch -f .jenkins/docker-compose.yml up -d nap_db"
            sh "docker-compose -p geosearch -f .jenkins/docker-compose.yml exec nap_db /bin/update-nap.sh"
        }, {
            step([$class: "JUnitResultArchiver", testResults: "reports/junit.xml"])

            sh "docker-compose -p geosearch -f .jenkins/docker-compose.yml down"
        }
    }

    stage("Build develop image") {
        tryStep "build", {
            def image = docker.build("build.datapunt.amsterdam.nl:5000/datapunt/geosearch:${env.BUILD_NUMBER}", "web")
            image.push()
            image.push("acceptance")
        }
    }
}

node {
    stage("Deploy to ACC") {
        tryStep "deployment", {
            build job: 'Subtask_Openstack_Playbook',
                    parameters: [
                            [$class: 'StringParameterValue', name: 'INVENTORY', value: 'acceptance'],
                            [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-geosearch.yml'],
                    ]
        }
    }
}


stage('Waiting for approval') {
    slackSend channel: '#ci-channel', color: 'warning', message: 'Geosearch is waiting for Production Release - please confirm'
    input "Deploy to Production?"
}



node {
    stage('Push production image') {
	tryStep "image tagging", {
	    def image = docker.image("build.datapunt.amsterdam.nl:5000/datapunt/geosearch:${env.BUILD_NUMBER}")
	    image.pull()

            image.push("production")
            image.push("latest")
        }
    }
}

node {
    stage("Deploy") {
        tryStep "deployment", {
            build job: 'Subtask_Openstack_Playbook',
                    parameters: [
                            [$class: 'StringParameterValue', name: 'INVENTORY', value: 'production'],
                            [$class: 'StringParameterValue', name: 'PLAYBOOK', value: 'deploy-geosearch.yml'],
                    ]
        }
    }
}
