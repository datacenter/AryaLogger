#!/usr/bin/env python
"""AryaLogger.

A small server based on SimpleAciUiLogServer that can convert APIC GUI logging
messages to ACI Python SDK (cobra) code.

Depends on SimpleAciUiLogServer, arya and acicobra/acimodel python modules.
"""

import logging
import os
import signal
import socket
import sys
import tempfile
from collections import OrderedDict, namedtuple
from urlparse import urlparse, ResultMixin, parse_qs
from argparse import ArgumentParser
from SimpleAciUiLogServer import ThreadingSimpleAciUiLogServer, serve_forever
from cobra.mit.naming import Dn
from arya import arya

SERVER_CERT = """
-----BEGIN RSA PRIVATE KEY-----
MIICXAIBAAKBgQC+oA+hYsF3uBIMt7i1ELfUFnyf4/MKM/Ylmy4yBc0/YhqANXYk
so3+gAGkgRlv9ODdsFS7KvjzyaT0kjgA3ahDPyvtroAOWsdFdHJvtS4Ek1WI1Bee
0hNZlTmjQgnjp9ENYl9ImGWghcubJhtse5cJhL9c/hq40do4llZjaaEiCQIDAQAB
AoGAYbd1K7qPCErAXeqT8aVXRo4cZm4YeSN3y4FH5faZZyNoCE7feCJbrZl6vhQ7
sOtrldi9JpD5uyaju4d00+TMSoFqnTuAYLg4CEUAkAq2Hgg1EfQfPpC8IgYdR5qQ
hRu0JArXldch1YLHw8GQGkkZe/cJXiHs/FPjmdUQSsydI50CQQDuEecLrSLjuMpE
i8xjD9cQxSDTHJFDZttVb08fjaKFJk993TsUR2t/eR92OR5m0CFei/RUyYpUaPbk
1s3Eau7XAkEAzPtnMMKoGR3qfLqXzfmgLwQA0UbeV8PbxRCkaCnSYcpn0qJH7UtS
Qjb4X6MPA9bNUnydWFgbPgz4MwKRo0q6HwJAP6DxS6GerZZ6GQ/0NJXLOWQ2fbYo
7QbUoGT7lMdaJJQ0ssMqQyVDifJpgkOJ6JjAEnD9gJvNKPpU4py2qkSaSQJANngr
0Jo5XwtDD0fqJPLLbRLsQLBLTxkdoj0s4v0SCahmdGNpJ5ZXUn8W+xryV3vR7bRt
f1dSTefWYH+zQagO0wJBANlNp79CN7ylgXdrhRVQmBsXHN4G8biUUxMYsfK4Ao/i
Ga3xtkYLv7OmrtY+Gx6w56Jqxyucaka8VBHK0/7JTLE=
-----END RSA PRIVATE KEY-----
-----BEGIN CERTIFICATE-----
MIID+jCCA2OgAwIBAgIJALUh5RwHQhJoMA0GCSqGSIb3DQEBBQUAMIGvMQswCQYD
VQQGEwJVUzELMAkGA1UECBMCQ0ExETAPBgNVBAcTCFNhbiBKb3NlMRUwEwYDVQQK
EwxhcGlpbnNwZWN0b3IxHTAbBgNVBAsTFFNpbXBsZUFjaVVpTG9nU2VydmVyMSow
KAYDVQQDEyFTaW1wbGVBY2lVaUxvZ1NlcnZlci5hcGlpbnNwZWN0b3IxHjAcBgkq
hkiG9w0BCQEWD210aW1tQGNpc2NvLmNvbTAgFw0xNTAxMjMwMDI1NDJaGA8zMDE0
MDUyNjAwMjU0Mlowga8xCzAJBgNVBAYTAlVTMQswCQYDVQQIEwJDQTERMA8GA1UE
BxMIU2FuIEpvc2UxFTATBgNVBAoTDGFwaWluc3BlY3RvcjEdMBsGA1UECxMUU2lt
cGxlQWNpVWlMb2dTZXJ2ZXIxKjAoBgNVBAMTIVNpbXBsZUFjaVVpTG9nU2VydmVy
LmFwaWluc3BlY3RvcjEeMBwGCSqGSIb3DQEJARYPbXRpbW1AY2lzY28uY29tMIGf
MA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC+oA+hYsF3uBIMt7i1ELfUFnyf4/MK
M/Ylmy4yBc0/YhqANXYkso3+gAGkgRlv9ODdsFS7KvjzyaT0kjgA3ahDPyvtroAO
WsdFdHJvtS4Ek1WI1Bee0hNZlTmjQgnjp9ENYl9ImGWghcubJhtse5cJhL9c/hq4
0do4llZjaaEiCQIDAQABo4IBGDCCARQwHQYDVR0OBBYEFN2EqumA49KSEPjLLSni
UtKth4zQMIHkBgNVHSMEgdwwgdmAFN2EqumA49KSEPjLLSniUtKth4zQoYG1pIGy
MIGvMQswCQYDVQQGEwJVUzELMAkGA1UECBMCQ0ExETAPBgNVBAcTCFNhbiBKb3Nl
MRUwEwYDVQQKEwxhcGlpbnNwZWN0b3IxHTAbBgNVBAsTFFNpbXBsZUFjaVVpTG9n
U2VydmVyMSowKAYDVQQDEyFTaW1wbGVBY2lVaUxvZ1NlcnZlci5hcGlpbnNwZWN0
b3IxHjAcBgkqhkiG9w0BCQEWD210aW1tQGNpc2NvLmNvbYIJALUh5RwHQhJoMAwG
A1UdEwQFMAMBAf8wDQYJKoZIhvcNAQEFBQADgYEABPx5cxBNOjWOxZbiRVfpzKac
MKs4tFNtEmilAY7kvNouGaSl1Yw2fCpGXjstOG0+SxPy34YgeQSVOGQI1KXhd7vk
nALqxrKiP2rzpZveBkjq5voRpFw2creEXyt76EKQgwRHYJP60Vu3bYnYNoFHdUwE
TOBaHjC6ZZLRd77dd3s=
-----END CERTIFICATE-----
"""


class ApicParseResult(namedtuple('ApicParseResult',
                                 'scheme netloc path params query fragment'),
                      ResultMixin):

    """ApicParseResult class.

    Mixin type of class that adds some apic specific properties to the urlparse
    named tuple
    """

    @property
    def dn_or_class(self):
        """Check if a path is for a dn or class."""
        pathparts = self._get_path_parts()
        if pathparts[1] != 'node':
            return self._get_dn_or_class(pathparts, 1)
        else:
            return self._get_dn_or_class(pathparts, 2)

    @property
    def api_format(self):
        """return the api format portion of the URL."""
        return self._get_api_format(self.path)

    @property
    def api_method(self):
        """Return the api method."""
        pathparts = self._get_path_parts()
        if pathparts[1] == 'node':
            return pathparts[2]
        else:
            return pathparts[1]

    @property
    def classnode(self):
        """Return the class or an empty string for mo queries."""
        if self.api_method != 'class':
            return ""
        pathparts = self._get_path_parts()
        if pathparts[1] != 'node':
            return self._get_classnode(pathparts, 3)
        else:
            return self._get_classnode(pathparts, 4)

    @staticmethod
    def _get_classnode(parts, index):
        """Get the class portion of a path."""
        if len(parts) <= index:
            return ""
        else:
            return "/".join(parts[index - 1:-1])

    def _get_path_parts(self):
        """Return a list of path parts."""
        dn_str = self._remove_format_from_path(self.path, self.api_format)
        dn_str = self._sanitize_path(dn_str)
        return dn_str[1:].split("/")

    @staticmethod
    def _remove_format_from_path(path, fmt):
        """Remove the api format from the path, including the ."""
        return path[:-len("." + fmt)]

    @staticmethod
    def _get_api_format(path):
        """Return either xml or json for the api format."""
        if path.endswith(".xml"):
            return 'xml'
        elif path.endswith(".json"):
            return 'json'

    @staticmethod
    def _get_dn_or_class(parts, index):
        """Return just the dn or the class."""
        if parts[index] == 'class':
            return parts[-1]
        elif parts[index] == 'mo':
            return "/".join(parts[index + 1:])
        else:
            return ""

    @staticmethod
    def _sanitize_path(path):
        """Left strip any / from the path."""
        return path.lstrip("/")


def apic_rest_urlparse(url):
    """Parse the APIC REST API URL."""
    atuple = urlparse(url)
    scheme, netloc, path, params, query, fragment = atuple
    return ApicParseResult(scheme, netloc, path, params, query, fragment)


def convert_dn_to_cobra(dn_str):
    """Convert an ACI distinguished name to ACI Python SDK (cobra) code."""
    cobra_dn = Dn.fromString(dn_str)
    parent_mo_or_dn = "''"
    dn_dict = OrderedDict()
    for rname in cobra_dn.rns:
        rn_str = str(rname)
        dn_dict[rn_str] = {}
        dn_dict[rn_str]['namingVals'] = tuple(rname.namingVals)
        dn_dict[rn_str]['moClassName'] = rname.meta.moClassName
        dn_dict[rn_str]['className'] = rname.meta.className
        dn_dict[rn_str]['parentMoOrDn'] = parent_mo_or_dn
        parent_mo_or_dn = rname.meta.moClassName
    cobra_str = ""
    for arn in dn_dict.items():
        if len(arn[1]['namingVals']) > 0:
            nvals = [str(val) for val in arn[1]['namingVals']]
            nvals_str = ", '" + ", ".join(nvals) + "'"
        else:
            nvals_str = ""
        cobra_str += "    # {0} = {1}({2}{3})\n".format(arn[1]['moClassName'],
                                                        arn[1]['className'],
                                                        arn[1]['parentMoOrDn'],
                                                        nvals_str)
    return cobra_str


def parse_apic_options_string(options):
    """Parse the REST API options string."""
    dictmap = {
        'rsp-prop-include':     'propInclude',
        'rsp-subtree-filter':   'subtreePropFilter',
        'rsp-subtree-class':    'subtreeClassFilter',
        'rsp-subtree-include':  'subtreeInclude',
        'query-target':         'queryTarget',
        'target-subtree-class': 'classFilter',
        'query-target-filter':  'propFilter',
        'rsp-subtree':          'subtree',
        'replica':              'replica',
        'target-class':         'targetClass',
    }
    qstring = ''
    if options is None or options == '':
        return qstring
    for opt, value in parse_qs(options).items():
        if opt in dictmap.keys():
            val_str = value[0].replace('"', '\"')
            qstring += '    query.{0} = "{1}"\n'.format(opt, val_str)
        else:
            qstring += ('    # Query option "{0}" is not'.format(opt) +
                        ' supported by Cobra SDK\n')
    return qstring


def get_dn_query(dn_str):
    """Get the dn query string."""
    cobra_str = "    query = cobra.mit.request.DnQuery('"
    cobra_str += str(dn_str)
    cobra_str += "')"
    return cobra_str


def get_class_query(kls):
    """Get the class query string."""
    cobra_str = "    query = cobra.mit.request.ClassQuery('"
    cobra_str += str(kls)
    cobra_str += "')"
    return cobra_str


def process_get(url):
    """Process a get request log message."""
    if 'subscriptionRefresh.json' in url:
        return
    if 'aaaRefresh.json' in url:
        return
    purl = apic_rest_urlparse(url)
    qstring = parse_apic_options_string(purl.query)
    cobra_str = ""
    if purl.api_method == 'mo':
        cobra_str2 = convert_dn_to_cobra(purl.dn_or_class)
        cobra_str2 += "    # Direct dn query:\n"
        cobra_str2 += get_dn_query(purl.dn_or_class)
        cobra_str2 += "\n"
        cobra_str += "SDK:\n\n    # Object instantiation:\n"
        cobra_str += "{0}".format(cobra_str2)
        cobra_str += "{0}\n".format(qstring)
    elif purl.api_method == 'class':
        if purl.classnode != "":
            cobra_str += ""
            cobra_str += "    # Cobra does not support APIC based node " + \
                         "queries at this time\n"
        else:

            cobra_str2 = ""
            cobra_str2 += "    # Direct class query:\n"
            cobra_str2 += get_class_query(purl.dn_or_class)
            cobra_str2 += "\n"
            cobra_str += "SDK:\n\n{0}".format(cobra_str2)
            cobra_str += "{0}\n".format(qstring)
    else:
        cobra_str = "\n# api method {0} not supported yet".format(
            purl.api_method)
    logging_str = "GET URL: {0}\n{1}".format(url, cobra_str)
    logging.debug(logging_str)


def undefined(**kwargs):
    """Process an undefined logging message."""
    process_get(kwargs['data']['url'])


def GET(**kwargs):   # pylint:disable=invalid-name
    """Process a GET logging message."""
    process_get(kwargs['data']['url'])


def POST(**kwargs):  # pylint:disable=invalid-name
    """Process a POST logging message."""
    url = kwargs['data']['url']
    payload = kwargs['data']['payload']
    purl = apic_rest_urlparse(url)
    arya_inst = arya()
    if purl.api_method != 'mo':
        logging.debug("Unknown api_method in POST: %s", purl.api_method)
        return

    cobra_str = arya_inst.getpython(jsonstr=payload)
    logging_str = "POST URL: %s\nPOST Payload:\n%s\nSDK:\n\n%s"
    logging.debug(logging_str, url, payload, cobra_str)


def EventChannelMessage(**kwargs):  # pylint:disable=C0103,W0613
    """Process an event channel logging message."""
    pass


def start_server(args):
    """Start the server threads."""
    # This is used to store the certificate filename
    cert = ""

    # Setup a signal handler to catch control-c and clean up the cert temp file
    # No way to catch sigkill so try not to do that.
    # noinspection PyUnusedLocal
    def sigint_handler(sig, frame):  # pylint:disable=unused-argument
        """A signal handler for interrupt."""
        if not args.cert:
            try:
                os.unlink(cert)
            except OSError:  # pylint:disable=pointless-except
                pass
        print "Exiting..."
        sys.exit(0)

    ThreadingSimpleAciUiLogServer.prettyprint = args.nice_output
    ThreadingSimpleAciUiLogServer.indent = args.indent

    http_server = ThreadingSimpleAciUiLogServer(("", args.port),
                                                logRequests=args.logrequests,
                                                location=args.location,
                                                excludes=args.exclude)
    # register our callback functions
    http_server.register_function(POST)
    http_server.register_function(GET)
    http_server.register_function(undefined)
    http_server.register_function(EventChannelMessage)

    if not args.cert:
        # Workaround ssl wrap socket not taking a file like object
        cert_file = tempfile.NamedTemporaryFile(delete=False)
        cert_file.write(SERVER_CERT)
        cert_file.close()
        cert = cert_file.name
        print("\n+++WARNING+++ Using an embedded self-signed certificate for " +
              "HTTPS, this is not secure.\n")
    else:
        cert = args.cert

    https_server = ThreadingSimpleAciUiLogServer(("", args.sslport),
                                                 cert=cert,
                                                 location=args.location,
                                                 logRequests=args.logrequests,
                                                 excludes=args.exclude)

    # register our callback functions
    https_server.register_function(POST)
    https_server.register_function(GET)
    https_server.register_function(undefined)
    https_server.register_function(EventChannelMessage)

    signal.signal(signal.SIGINT, sigint_handler)  # Or whatever signal

    # This simply sets up a socket for UDP which has a small trick to it.
    # It won't send any packets out that socket, but this will allow us to
    # easily and quickly interogate the socket to get the source IP address
    # used to connect to this subnet which we can then print out to make for
    # and easy copy/paste in the APIC UI.
    ip_addr = [(s.connect((args.apicip, 80)), s.getsockname()[0], s.close())
               for s in [socket.socket(socket.AF_INET,
                                       socket.SOCK_DGRAM)]][0][1]
    print("serving at:")  # pylint:disable=C0325
    print("http://{0}:{1}{2}".format(str(ip_addr), str(args.port),
                                     str(args.location)))
    print("https://{0}:{1}{2}".format(str(ip_addr), str(args.sslport),
                                      str(args.location)))
    print("")  # pylint:disable=C0325
    print("Make sure your APIC(s) are configured to send log messages: " +
          "welcome username -> Start Remote Logging")
    print("Note: If you connect to your APIC via HTTPS, configure the " +
          "remote logging to use the https server.")
    serve_forever([http_server, https_server])


def main():
    """The main function run when AryaLogger is run in standalone mode."""
    parser = ArgumentParser('Archive APIC Rest API calls in the PythonSDK ' +
                            'syntax')
    parser.add_argument('-a', '--apicip', required=False, default='8.8.8.8',
                        help=('If you have a multihomed system, where the ' +
                              'apic is on a private network, the server ' +
                              'will print the ip address your local system ' +
                              'has a route to 8.8.8.8.  If you want the ' +
                              'server to print a more accurate ip address ' +
                              'for theserver you can tell it the apicip ' +
                              'address.'))

    parser.add_argument('-po', '--port', type=int, required=False,
                        default=8987,
                        help='Local port to listen on, default=8987')

    parser.add_argument('-l', '--location', default="/apiinspector",
                        required=False,
                        help=('Location that transaction logs are being ' +
                              'sent to, default=/apiinspector'))

    parser.add_argument('-s', '--sslport', type=int, required=False,
                        help=('Local port to listen on for ssl connections, ' +
                              ' default=8443'))

    parser.add_argument('-c', '--cert', type=str, required=False,
                        help=('The server certificate file for ssl ' +
                              'connections, default="server.pem"'))

    parser.add_argument('-e', '--exclude', action='append', nargs='*',
                        default=[], choices=['subscriptionRefresh',
                                             'aaaRefresh', 'topInfo'],
                        help=('Exclude certain types of common "noise" ' +
                              'queries.'))

    parser.add_argument('-r', '--logrequests', action='store_true',
                        default=False, required=False,
                        help=('Log server requests and response codes to ' +
                              'standard error'))

    parser.add_argument('-n', '--nice-output', action='store_true',
                        default=False, required=False,
                        help='Pretty print the response and payload')

    parser.add_argument('-i', '--indent', type=int, default=2, required=False,
                        help=('The number of spaces to indent when pretty ' +
                              'printing'))

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - \n%(message)s')

    if args.exclude:
        # Flatten the list
        args.exclude = [val for sublist in args.exclude for val in sublist]

    start_server(args)


if __name__ == '__main__':
    main()
