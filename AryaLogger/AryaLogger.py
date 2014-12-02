#!/usr/bin/env python

import socket
import cgi
from collections import OrderedDict, namedtuple
from urlparse import urlparse, ResultMixin
from StringIO import StringIO
from argparse import ArgumentParser
from SimpleAciUiLogServer import SimpleAciUiLogServer
from cobra.mit.naming import Dn
from arya import arya

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

    def _get_classnode(self, parts, index):
        if len(parts) <= index:
            return ""
        else:
            return "/".join(parts[index-1:-1])

    def _get_path_parts(self):
        dn = self._remove_format_from_path(self.path, self.api_format)
        dn = self._sanitize_path(dn)
        return dn[1:].split("/")

    def _remove_format_from_path(self, path, format):
        return path[:-len("." + format)]

    def _get_api_format(self, path):
        if path.endswith(".xml"):
            return 'xml'
        elif path.endswith(".json"):
            return 'json'

    def _get_dn_or_class(self, parts, index):
        if parts[index] == 'class':
            return parts[-1]
        elif parts[index] == 'mo':
            return "/".join(parts[index+1:])
        else:
            return ""

    def _sanitize_path(self, path):
        return path.lstrip("/")

def apic_rest_urlparse(url):
    tuple = urlparse(url)
    scheme, netloc, path, params, query, fragment = tuple
    return ApicParseResult(scheme, netloc, path, params, query, fragment)

def convert_dn_to_cobra(dn):
    cobra_dn = Dn.fromString(dn)
    parentMoOrDn = "''"
    dn_dict = OrderedDict()
    for rn in cobra_dn._Dn__rns:
        rn_str = str(rn)
        dn_dict[rn_str] = {}
        dn_dict[rn_str]['namingVals'] = rn._Rn__namingVals
        dn_dict[rn_str]['moClassName'] = rn._Rn__meta.moClassName
        dn_dict[rn_str]['className'] = rn._Rn__meta.className
        dn_dict[rn_str]['parentMoOrDn'] = parentMoOrDn
        parentMoOrDn = rn._Rn__meta.moClassName
    cobra_str = ""
    for arn in dn_dict.items():
        if len(arn[1]['namingVals']) > 0:
            nvals_str = ", '" + ", ".join(map(str, arn[1]['namingVals'])) + "'"
        else:
            nvals_str = ""
        cobra_str +=  "    # {0} = {1}({2}{3})\n".format(arn[1]['moClassName'],
                                                         arn[1]['className'],
                                                         arn[1]['parentMoOrDn'],
                                                        nvals_str)
    return cobra_str


def parse_apic_options_string(options):
    # TODO: Need to finish this.
    # cgi FieldStorage/MiniFieldStorage objects in a form container
    form = cgi.FieldStorage(
        fp=StringIO(options),
        #headers=self.headers,
        environ=dict(REQUEST_METHOD='POST',
                     CONTENT_TYPE='text/ascii',
        )
    )
    return form

def get_dn_query(dn):
    cobra_str = "    dnQuery = cobra.mit.request.DnQuery('"
    cobra_str += str(dn)
    cobra_str += "')"
    return cobra_str


def get_class_query(kls):
    cobra_str = "    classQuery = cobra.mit.request.ClassQuery('"
    cobra_str += str(kls)
    cobra_str += "')"
    return cobra_str


def process_get(url):
    if 'subscriptionRefresh.json' in url:
        return
    if 'aaaRefresh.json' in url:
        return
    purl = apic_rest_urlparse(url)

    cobra_str = ""
    if purl.api_method == 'mo':
        cobra_str += convert_dn_to_cobra(purl.dn_or_class)
        cobra_str += "    # Or direct dn query:\n"
        cobra_str += get_dn_query(purl.dn_or_class)
        cobra_str += "\n"
    elif purl.api_method == 'class':
        if purl.classnode != "":
            cobra_str += ""
            cobra_str += "    # Cobra does not support APIC based node " + \
                         "queries at this time\n"
        else:
            cobra_str += ""
            cobra_str += "    # Or direct class query:\n"
            cobra_str += get_class_query(purl.dn_or_class)
            cobra_str += "\n"
    else:
        cobra_str = "\n# api method {0} not supported yet".format(
            purl.api_method)
    print "GET URL: {0}".format(url)
    print "SDK:\n\n    # Object instantiation:\n{0}".format(cobra_str)


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
        print "Unknown api_method in POST: {0}".format(purl.api_method)
        return

    #cobra_str = convert_dn_to_cobra(purl.dn_or_class)
    cobra_str = a.getpython(jsonstr=payload)
    print "POST URL: {0}".format(url)
    print "POST Payload:\n{0}".format(payload)
    print "SDK:\n\n{0}".format(cobra_str)

def EventChannelMessage(**kwargs):
    #print "ignoring EventChannelMessage\n"
    # Ignore all Event Channel Messages
    pass


def start_server(args):
    server = SimpleAciUiLogServer(("", args.port),
                                  logRequests=args.logrequests,
                                  location=args.location)
    # register our callback functions
    server.register_function(POST)
    server.register_function(GET)
    server.register_function(undefined)
    server.register_function(EventChannelMessage)

    # This simply sets up a socket for UDP which has a small trick to it.
    # It won't send any packets out that socket, but this will allow us to
    # easily and quickly interogate the socket to get the source IP address
    # used to connect to this subnet which we can then print out to make for
    # and easy copy/paste in the APIC UI.
    ip = [(s.connect((args.apicip, 80)), s.getsockname()[0], s.close()) for s
          in [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]][0][1]
    print "serving at:"
    print "http://" + str(ip) + ":" + str(args.port) + args.location
    print
    server.serve_forever()

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
    parser.add_argument('-r', '--logrequests', help='Log server requests and ' +
                                                    'response codes to ' +
                                                    'standard error',
                        action='store_true', default=False, required=False)
    parser.add_argument('-u', '--username', help='Username for APIC account ' +
        'to be pre-populated in generated code', required=False,
        default='admin')
    parser.add_argument('-pa', '--password', help='Password for APIC account ' +
        ' to be pre-populated in generated code', required=False,
        default='password')
    args = parser.parse_args()

    start_server(args)


if __name__ == '__main__':
    main()