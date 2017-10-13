# encoding: utf-8
import os
import gc 
import re
import sys
import ast
import xml
import time
import logging
import utils
import json
import docker

# Initialize logging
logger = utils.setup_logger(appname="docker_stats", level=logging.INFO)

# Establish NAMESPACE
NAMESPACE = utils.NAMESPACE

# Disable stdout buffering
os.environ['PYTHONUNBUFFERED'] = '1'
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
gc.garbage.append(sys.stdout)

SCHEME = """
<scheme>
    <title>Docker Stats</title>
    <description>Runs the "docker stats" command and pulls performance information on active containers</description>
    <use_external_validation>true</use_external_validation>
    <streaming_mode>xml</streaming_mode>

    <endpoint>
        <args>
            <arg name="DOCKER_HOST">
                <title>URL of Docker server</title>
                <description>For example, unix:///var/run/docker.sock or tcp://127.0.0.1:1234. See output of "docker-machine env default".</description>
            </arg>
            <arg name="DOCKER_TLS_VERIFY">
                <title>Enable TLS</title>
                <description>For example, 1 or 0. See output of "docker-machine env default".</description>
            </arg>
            <arg name="DOCKER_CERT_PATH">
                <title>File path of docker certs</title>
                <description>See output of "docker-machine env default".</description>
            </arg>
            <arg name="containers">
                <title>Containers to monitor</title>
                <description>Specify containers (IDs or names) to monitor. For multiple containers, use a comma-separated list. Default: all</descrption>
            </arg>
        </args>
    </endpoint>
</scheme>
"""

def unicode_to_str(dict):
    """
    Helper function to convert a unicode dictionary into a string dictionary.
    """
    pass

def do_scheme():
    print SCHEME
    
def validate_arguments():
    # TODO
    pass

def usage():
    # TODO
    pass

# Read XML configuration passed from splunkd
def get_config():
    config_str = sys.stdin.read()
    return utils.get_config(config_str)

# print XML stream with event time and sourcetype
def print_xml_stream(sourcetype, data):
    print "<stream><event><sourcetype>%s</sourcetype><data>%s</data></event></stream>" \
    % (sourcetype, xml.sax.saxutils.escape(data))

# Convert a timestamp to epoch (example input format: "2016-08-30T12:08:54.123456Z")
def make_epoch(date_str):
    if "null" in date_str:
        return 0
    pattern = '%Y-%m-%dT%H:%M:%S'
    timestamp = date_str.split(".")[0]
    return int(time.mktime(time.strptime(timestamp, pattern)))

def run():
    if len(sys.argv) > 1:
        try:
            if sys.argv[1] == "--scheme":
                do_scheme()
            elif sys.argv[1] == "--validate-arguments":
                validate_arguments()
            else:
                usage()
        except Exception as ex:
            logger.critical(ex)
    else:  
        # Get configs
        configs = get_config()

        # Get modinput name
        name = configs["name"]
        logger.info("Modular input [%s] data collection in progress..." % configs["name"])

        # Try to instantiate the docker client
        try:
            os.environ["DOCKER_HOST"] = configs["DOCKER_HOST"]
            os.environ["DOCKER_TLS_VERIFY"] = configs["DOCKER_TLS_VERIFY"]
            os.environ["DOCKER_CERT_PATH"] = configs["DOCKER_CERT_PATH"]
            client = docker.from_env()
        except:
            raise

        # Get list of containers to monitor
        if hasattr(configs, "containers"):
            containers = configs["containers"].strip()
            if (containers == "*") or (containers.lower() == "all"):
                containers = "all"
            else:
                containers = containers.split(",")
        else:
            containers = "all"
        logger.info("Containers to monitor: %s" % containers)
        
        try:
            # Get all active containers and compare to the ones defined in the modinput arguments
            if containers is not "all":
                container_set = set(containers)
                active_ids = [str(c.id)[0:12] for c in client.containers.list()]
                active_names = [str(c.name) for c in client.containers.list()]
                remainder = container_set.difference(active_ids).difference(active_names)
                logger.warn("Specified containers are not active, therefore not collecting stats: %s" % remainder)
                # Get the result of original container_set - remainder
                container_set = container_set.difference(remainder)
            else:
                container_set = set([str(c.name) for c in client.containers.list()])
            logger.info("Grabbing stats for container list: %s" % container_set)

            # Get container stats
            for cont in container_set:
                logger.info("Getting data in container: %s" % cont)
                data = client.containers.get(cont).stats(decode=True, stream=False)
                # Default output from docker-py will return "/pensive_payne", so just removing the "/"
                data["name"] = data["name"].lstrip("/")
                # Send to XML stream to index the data
                print_xml_stream(sourcetype="docker:stats", data=json.dumps(data))

        except Exception as ex:
            logger.critical(ex)
        finally:
            logger.info("Terminating modular input: %s" % name)

if __name__ == '__main__':
    logger.info("Initiating docker_stats modular input command: %s" % sys.argv)
    try:
        run()
    except Exception as ex:
        logger.critical(ex)
    finally:
        logger.info("Finished docker_stats modular input")
