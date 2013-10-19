#!/usr/bin/env python
"""
SAML ECP client implementation - by Giovanni Bajo
Based on ecp.py provided by the Shibboleth project

This module implements a SAML 2.0 ECP client, to allow
applications to authenticate and then communicate to
services protected by SAML.

It requires that both the SP and the IdP support the ECP
profile to allow for browserless communication.
"""
import os
import sys
import stat
import urllib2
import cookielib
import re
import getpass
import time

# LXML is required because of better namespace handling. Specifically,
# we need to deserialize a XML including namespaces, parse it, and then
# serialize it back unsing the exact smae namespace prefixes (because it
# contains a digital signature, that would otherwise get broken). This is 
# impossible to achieve with Python 2.7 ElementTree, that doesn't preserve
# namespace prefixes.
from lxml import etree
from copy import deepcopy

class SamlEcpError(RuntimeError):
    pass

def auth(idp_endpoint, sp_target, login, password):
    """
    Given an IdP endpoint for ECP, the desired target
    from the SP, and a login to use against the IdP
    manage an ECP exchange with the SP and the IdP
    and return a urllib2 opener (with a cookie jar)
    that can be used for further communcation with the SP.
    """
    # create a cookie jar and cookie handler
    cookie_handler = urllib2.HTTPCookieProcessor()

    # need an instance of HTTPS handler to do HTTPS
    httpsHandler = urllib2.HTTPSHandler(debuglevel = 0)

    # create the base opener object
    opener = urllib2.build_opener(cookie_handler, httpsHandler)

    # headers needed to indicate to the SP an ECP request
    headers = {
        'Accept' : 'text/html; application/vnd.paos+xml',
        'PAOS'   : 'ver="urn:liberty:paos:2003-08";"urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp"'
    }

    # request target from SP 
    request = urllib2.Request(url=sp_target, headers=headers)

    try:
        response = opener.open(request)
    except Exception, e:
        raise SamlEcpError("cannot connect to SP (%s)" % sp_target)

    # convert the SP resonse from string to etree Element object
    try:
        sp_response = etree.XML(response.read())
    except Exception, e:
        raise SamlEcpError("invalid response from SP (%s) -- %s" % (sp_target, e))

    # pick out the relay state element from the SP so that it can
    # be included later in the response to the SP
    namespaces = {
        'ecp' : 'urn:oasis:names:tc:SAML:2.0:profiles:SSO:ecp',
        'S'   : 'http://schemas.xmlsoap.org/soap/envelope/',
        'paos': 'urn:liberty:paos:2003-08'
    }

    try:
        relay_state = sp_response.xpath("//ecp:RelayState", namespaces=namespaces)[0]
        response_consumer_url = sp_response.xpath("/S:Envelope/S:Header/paos:Request/@responseConsumerURL", namespaces=namespaces)[0]
    except Exception, e:
        raise SamlEcpError("invalid response from SP (%s) -- %s" % (sp_target, e))

    # make a deep copy of the SP response and then remove the header
    # in order to create the package for the IdP
    idp_request = deepcopy(sp_response)
    header = idp_request[0]
    idp_request.remove(header)

    # create a password manager
    # and basic auth handler to add to the existing opener
    password_mgr = urllib2.HTTPPasswordMgrWithDefaultRealm()
    password_mgr.add_password(None, idp_endpoint, login, password)
    auth_handler = urllib2.HTTPBasicAuthHandler(password_mgr)
    opener.add_handler(auth_handler)

    # POST the request to the IdP 
    headers = {
        "Content-Type": "text/xml"
    }
    request = urllib2.Request(idp_endpoint, headers=headers, data=etree.tostring(idp_request))
    request.get_method = lambda: 'POST'

    try:
        response = opener.open(request)
    except urllib2.HTTPError, e:
        if e.code == 401:
            raise
        raise SamlEcpError("invalid response from SP (%s) -- %s" % (sp_target, e))
    except Exception, e:
        raise SamlEcpError("invalid response from IdP (%s) -- %s" % (idp_endpoint, e))

    try:
        idp_response = etree.XML(response.read())
    except Exception, e:
        raise SamlEcpError("invalid response from IdP (%s) -- %s" % (sp_target, e))

    try:
        assertion_consumer_service = idp_response.findall("S:Header/ecp:Response", namespaces=namespaces)[0].get("AssertionConsumerServiceURL")
    except Exception,e:
        raise SamlEcpError("invalid response from IdP (%s) -- %s" % (sp_target, e))

    # if the assertionConsumerService attribute from the IdP 
    # does not match the responseConsumerURL from the SP
    # we cannot trust this exchange so send SOAP 1.1 fault
    # to the SP and exit
    if assertion_consumer_service != response_consumer_url:        
        soap_fault = """
            <S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
               <S:Body>
                 <S:Fault>
                    <faultcode>S:Server</faultcode>
                    <faultstring>responseConsumerURL from SP and assertionConsumerServiceURL from IdP do not match</faultstring>
                 </S:Fault>
               </S:Body>
            </S:Envelope>
            """

        headers = {
            'Content-Type' : 'application/vnd.paos+xml',
        }
        
        request = urllib2.Request(url=response_consumer_url, data=soap_fault, headers=headers)
        request.get_method = lambda: 'POST'

        # POST the SOAP 1.1 fault to the SP and ignore any return 
        try:
            response = opener.open(request)
        except Exception, e:
            pass

        print >>sys.stderr, assertion_consumer_service
        print >>sys.stderr, response_consumer_url
        raise SamlEcpError("warning: mismatch in consumer URLs between SP and IdP -- configuration error?")

    # make a deep cop of the IdP response and replace its
    # header contents with the relay state initially sent by
    # the SP
    sp_package = deepcopy(idp_response)
    sp_package[0][0] = relay_state

    headers = {
       'Content-Type' : 'application/vnd.paos+xml',
    }

    # POST the package to the SP
    request = urllib2.Request(url=assertion_consumer_service, data=etree.tostring(sp_package), headers=headers)
    request.get_method = lambda: 'POST'

    try:
        response = opener.open(request)
    except Exception, e:
        raise SamlEcpError("invalid second response from SP (%s)" % sp_target)

    # We're done, return the opener
    return opener

if __name__ == "__main__":
    main()

    
