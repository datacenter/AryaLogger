#!/usr/bin/env python

import logging
import os
import signal
import socket
import sys
import tempfile
from collections import OrderedDict, namedtuple
from urlparse import urlparse, ResultMixin, parse_qs
from StringIO import StringIO
from argparse import ArgumentParser
from SimpleAciUiLogServer import ThreadingSimpleAciUiLogServer, serve_forever
from cobra.mit.naming import Dn
from arya import arya

server_cert = """
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
    """
    Mixin type of class that adds some apic specific properties to the urlparse
    named tuple
    """
    @property
    def dn_or_class(self):
        pathparts = self._get_path_parts()
        if pathparts[1] != 'node':
            return self._get_dn_or_class(pathparts, 1)
        else:
            return self._get_dn_or_class(pathparts, 2)

    @property
    def api_format(self):
        return self._get_api_format(self.path)

    @property
    def api_method(self):
        pathparts = self._get_path_parts()
        if pathparts[1] == 'node':
            return pathparts[2]
        else:
            return pathparts[1]

    @property
    def classnode(self):
        if self.api_method != 'class':
            return ""
        pathparts = self._get_path_parts()
        if pathparts[1] != 'node':
            return self._get_classnode(pathparts, 3)
        else:
            return self._get_classnode(pathparts, 4)

    @staticmethod
    def _get_classnode(parts, index):
        if len(parts) <= index:
            return ""
        else:
            return "/".join(parts[index-1:-1])

    def _get_path_parts(self):
        dn = self._remove_format_from_path(self.path, self.api_format)
        dn = self._sanitize_path(dn)
        return dn[1:].split("/")

    @staticmethod
    def _remove_format_from_path(path, fmt):
        return path[:-len("." + fmt)]

    @staticmethod
    def _get_api_format(path):
        if path.endswith(".xml"):
            return 'xml'
        elif path.endswith(".json"):
            return 'json'

    @staticmethod
    def _get_dn_or_class(parts, index):
        if parts[index] == 'class':
            return parts[-1]
        elif parts[index] == 'mo':
            return "/".join(parts[index+1:])
        else:
            return ""

    @staticmethod
    def _sanitize_path(path):
        return path.lstrip("/")


def apic_rest_urlparse(url):
    atuple = urlparse(url)
    scheme, netloc, path, params, query, fragment = atuple
    return ApicParseResult(scheme, netloc, path, params, query, fragment)


def convert_dn_to_cobra(dn):
    cobra_dn = Dn.fromString(dn)
    parentMoOrDn = "''"
    dn_dict = OrderedDict()
    for rn in cobra_dn.rns:
        rn_str = str(rn)
        dn_dict[rn_str] = {}
        dn_dict[rn_str]['namingVals'] = tuple(rn.namingVals)
        dn_dict[rn_str]['moClassName'] = rn.meta.moClassName
        dn_dict[rn_str]['className'] = rn.meta.className
        dn_dict[rn_str]['parentMoOrDn'] = parentMoOrDn
        parentMoOrDn = rn.meta.moClassName
    cobra_str = ""
    for arn in dn_dict.items():
        if len(arn[1]['namingVals']) > 0:
            nvals_str = ", '" + ", ".join(map(str, arn[1]['namingVals'])) + "'"
        else:
            nvals_str = ""
        cobra_str += "    # {0} = {1}({2}{3})\n".format(arn[1]['moClassName'],
                                                        arn[1]['className'],
                                                        arn[1]['parentMoOrDn'],
                                                        nvals_str)
    return cobra_str


def parse_apic_options_string(options):
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
        if opt == 'subscription':
            qstring += '    # Query option "subscription" is not supported by Cobra SDK\n'
        else:
            if opt not in dictmap.keys():
                raise ValueError("Unknown REST query option: {0}: {1}".format(opt, value))
            qstring += '    query.{0} = "{1}"\n'.format(opt, value[0].replace('"', '\"'))
    return qstring

def get_dn_query(dn):
    cobra_str = "    query = cobra.mit.request.DnQuery('"
    cobra_str += str(dn)
    cobra_str += "')"
    return cobra_str


def get_class_query(kls):
    cobra_str = "    query = cobra.mit.request.ClassQuery('"
    cobra_str += str(kls)
    cobra_str += "')"
    return cobra_str


def process_get(url):
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
        cobra_str += "SDK:\n\n    # Object instantiation:\n{0}".format(cobra_str2)
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
    process_get(kwargs['data']['url'])
    #pass


def GET(**kwargs):
    process_get(kwargs['data']['url'])
    #pass


def POST(**kwargs):
    url = kwargs['data']['url']
    payload = kwargs['data']['payload']
    purl = apic_rest_urlparse(url)
    a = arya()
    if purl.api_method != 'mo':
        logging.debug("Unknown api_method in POST: {0}".format(purl.api_method))
        return

    #cobra_str = convert_dn_to_cobra(purl.dn_or_class)
    cobra_str = a.getpython(jsonstr=payload)
    logging_str = "POST URL: {0}\nPOST Payload:\n{1}\nSDK:\n\n{2}".format(url,
                                                                      payload,
                                                                      cobra_str)
    logging.debug(logging_str)


def EventChannelMessage(**kwargs):
    #logging.debug("ignoring EventChannelMessage\n")
    # Ignore all Event Channel Messages
    pass


def start_server(args):

    # This is used to store the certificate filename
    cert = ""

    # Setup a signal handler to catch control-c and clean up the cert temp file
    # No way to catch sigkill so try not to do that.
    # noinspection PyUnusedLocal
    def sigint_handler(sig, frame):
        if not args.cert:
            try:
                os.unlink(cert)
            except OSError:
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
        cert_file.write(server_cert)
        cert_file.close()
        cert = cert_file.name
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
    ip = [(s.connect((args.apicip, 80)), s.getsockname()[0], s.close()) for s
          in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    print("serving at:")
    print("http://{0}:{1}{2}".format(str(ip), str(args.port), str(args.location)))
    print("https://{0}:{1}{2}".format(str(ip), str(args.sslport), str(args.location)))
    print("")
    serve_forever([http_server, https_server])

def main():
    parser = ArgumentParser('Archive APIC Rest API calls in the PythonSDK ' +
                            'syntax')
    parser.add_argument('-a', '--apicip', help='If you have a multihomed ' +
                                               'system, where the apic is ' +
                                               'on a private network, the ' +
                                               'server will print the ' +
                                               'ip address your local ' +
                                               'system has a route to ' +
                                               '8.8.8.8.  If you want the ' +
                                               'server to print a more ' +
                                               'accurate ip address for ' +
                                               'the server you can tell it ' +
                                               'the apicip address.',
                        required=False, default='8.8.8.8')
    parser.add_argument('-po', '--port', help='Local port to listen on,' +
                                              ' default=8987', default=8987,
                        type=int, required=False)
    parser.add_argument('-l', '--location', help='Location that transaction ' +
                                                 'logs are being sent to, ' +
                                                 'default=/apiinspector',
                        default="/apiinspector", required=False)
    parser.add_argument('-s', '--sslport', help='Local port to listen on ' +
                                                ' for ssl connections, ' +
                                                ' default=8443', default=8443,
                        type=int, required=False)
    parser.add_argument('-c', '--cert', help='The server certificate file' +
                                             ' for ssl connections, ' +
                                             ' default="server.pem"',
                        type=str, required=False)
    parser.add_argument('-e', '--exclude', action='append', nargs='*',
                        default=[], choices=['subscriptionRefresh',
                                             'aaaRefresh', 'topInfo'],
                        help='Exclude certain types of common "noise" queries.')
    parser.add_argument('-r', '--logrequests', help='Log server requests and ' +
                                                    'response codes to ' +
                                                    'standard error',
                        action='store_true', default=False, required=False)
    parser.add_argument('-n', '--nice-output', help='Pretty print the ' +
                                                    'response and payload',
                        action='store_true', default=False, required=False)
    parser.add_argument('-i', '--indent', help='The number of spaces to ' +
                                               'indent when pretty ' +
                                               'printing',
                        type=int, default=2, required=False)
    #parser.add_argument('-u', '--username', help='Username for APIC account ' +
    #                                             'to be pre-populated in ' +
    #                                             'generated code',
    #                    required=False, default='admin')
    #parser.add_argument('-pa', '--password', help='Password for APIC account ' +
    #                                              'to be pre-populated in ' +
    #                                              'generated code',
    #                    required=False, default='password')
    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s - \n%(message)s')

    if args.exclude:
        # Flatten the list
        args.exclude = [val for sublist in args.exclude for val in sublist]

    start_server(args)


if __name__ == '__main__':
    main()

