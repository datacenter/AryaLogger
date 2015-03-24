#!/usr/bin/env python
"""
An example of converting from a dn string to APIC Cobra Python SDK.

Written by Mike Timm (mtimm@cisco.com)

Copyright (C) 2014 Cisco Systems Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from urlparse import urlparse, ResultMixin
from collections import OrderedDict, namedtuple
from cobra.mit.naming import Dn


class ApicParseResult(namedtuple('ApicParseResult',
                                 'scheme netloc path params query fragment'),
                      ResultMixin):
    """ApicParseResult.

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
        return dn[1:].split("/")

    def _remove_format_from_path(self, path, fmt):
        return path[:-len("." + fmt)]

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

def apic_rest_urlparse(url_str):
    tpl = urlparse(url_str)
    scheme, netloc, path, params, query, fragment = tpl
    return ApicParseResult(scheme, netloc, path, params, query, fragment)

def convert_dn_to_cobra(dn):
    cobra_dn = Dn.fromString(dn)
    parentMoOrDn = "''"
    dn_dict = OrderedDict()
    for rn in cobra_dn.rns:
        rn_str = str(rn)
        dn_dict[rn_str] = {}
        dn_dict[rn_str]['namingVals'] = rn.namingVals
        dn_dict[rn_str]['moClassName'] = rn.meta.moClassName
        dn_dict[rn_str]['className'] = rn.meta.className
        dn_dict[rn_str]['parentMoOrDn'] = parentMoOrDn
        parentMoOrDn = rn.meta.moClassName
    for arn in dn_dict.items():
        if len(arn[1]['namingVals']) > 0:
            nvals_str = ", '" + ", ".join(map(str, arn[1]['namingVals'])) + "'"
        else:
            nvals_str = ""
        print "{0} = {1}({2}{3})".format(arn[1]['moClassName'],
                                         arn[1]['className'],
                                         arn[1]['parentMoOrDn'],
                                         nvals_str)


if __name__ == '__main__':
    convert_dn_to_cobra('topology/HDfabricOverallHealth5min-0')
    print
    convert_dn_to_cobra('uni/tn-mgmt/mgmtp-default/oob-default')
    print

    url = 'https://10.122.254.211/api/node/mo/topology/HDfabricOverallHealt' + \
          'h5min-0.json'

    convert_dn_to_cobra(apic_rest_urlparse(url).dn_or_class)
    print

    url = 'https://10.122.254.211/api/node/mo/uni/tn-mgmt/mgmtp-default/oob' + \
          '-default.json'
    convert_dn_to_cobra(apic_rest_urlparse(url).dn_or_class)
    print
