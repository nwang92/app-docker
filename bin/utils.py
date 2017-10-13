import xml.dom.minidom
import splunk.appserver.mrsparkle.lib.util as util
import logging.handlers


NAMESPACE = "splunk_app_docker"


def setup_logger(appname=NAMESPACE, level=logging.INFO):
    """
    Setup a logger for the REST handler.
    """
    logger = logging.getLogger(appname)
    if len(logger.handlers) > 0: # Return existing logger if there is one already configured
        return logger
    logger.propagate = False # Prevent the log messages from being duplicated in the python.log file
    logger.setLevel(level)

    file_handler = logging.handlers.RotatingFileHandler(util.make_splunkhome_path(['var', 'log', 'splunk', '%s.log' % appname]), maxBytes=25000000, backupCount=5)

    formatter = logging.Formatter('%(asctime)s %(levelname)s [%(name)s] [%(module)s] [%(funcName)s] line:[%(lineno)d] [%(process)d]'
                             ' %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger


def get_config(config_str):
    config = {}
    try:
        doc = xml.dom.minidom.parseString(config_str.strip())
        server_uri = doc.getElementsByTagName("server_uri")[0]
        session_key = doc.getElementsByTagName("session_key")[0]
        config["server_uri"] = server_uri.childNodes[0].nodeValue
        config["session_key"] = session_key.childNodes[0].nodeValue
        
        root = doc.documentElement
        conf_node = root.getElementsByTagName("configuration")[0]
        if conf_node:
            stanza = conf_node.getElementsByTagName("stanza")[0]
            if stanza:
                stanza_name = stanza.getAttribute("name")
                if stanza_name:
                    config["name"] = stanza_name

                    params = stanza.getElementsByTagName("param")
                    for param in params:
                        param_name = param.getAttribute("name")
                        if param_name and param.firstChild and \
                           param.firstChild.nodeType == param.firstChild.TEXT_NODE:
                            data = param.firstChild.data
                            config[param_name] = data

        if not config:
            raise Exception, "Invalid configuration received from Splunk."

    except Exception, e:
        raise Exception, "Error getting Splunk configuration via STDIN: %s" % str(e)

    return config