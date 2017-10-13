[docker_stats://<name>]
* Modular input name

DOCKER_HOST = <value>
* URL of the docker server (ex: unix:///var/run/docker.sock or tcp://127.0.0.1:2376)
* Enter value as seen when running "docker-machine env <name>"
* required

DOCKER_TLS_VERIFY = <value>
* 1 or 0 if TLS is enabled
* Enter value as seen when running "docker-machine env <name>"
* required

DOCKER_CERT_PATH = <value>
* File path of server/client certs
* Enter value as seen when running "docker-machine env <name>"
* required

containers = <value>
* Comma-separated list of containers to monitor (ID or name)
