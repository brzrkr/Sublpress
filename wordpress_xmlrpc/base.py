import sublime, sublime_plugin
import os, sys, threading, zipfile, re, pprint, subprocess, collections, string, time, operator
from .compat import xmlrpc_client, dict_type, http_client
from .exceptions import ServerConnectionError, UnsupportedXmlrpcMethodError, InvalidCredentialsError, XmlrpcDisabledError
   
class sublUnmarshaller(xmlrpc_client.Unmarshaller):
    def start(self, tag, attrs):
        # prepare to handle this element
        if tag == "array" or tag == "struct":
            self._marks.append(len(self._stack))
        self._data = []
        self._value = (tag == "value")

    def end(self, tag, join=None):
        # call the appropriate end tag handler
        try:
            f = self.dispatch[tag]
        except KeyError:
            pass # unknown tag ?
        else:
            return f(self, string.join(self._data, ""))

if sys.version_info[0] == 3:
    class OurTransport(xmlrpc_client.Transport):
        def send_request(self, connection, handler, request_body, debug):
            return super(OurTransport, self).send_request(connection, handler, request_body, debug)

        def send_host(self, connection, host):
            return super(OurTransport, self).send_host(connection, host)

        def make_connection(self, host):
            #return an existing connection if possible.  This allows
            #HTTP/1.1 keep-alive.
            #if self._connection and host == self._connection[0]:
                #return self._connection[1]
            # create a HTTP connection object from a host descriptor
            chost, self._extra_headers, x509 = self.get_host_info(host)
            self._connection = host, http_client.HTTPConnection(chost)  
            return self._connection[1]

        def single_request(self, host, handler, request_body, verbose=False):
            # issue XML-RPC request
            try:
                http_conn = self.send_request(host, handler, request_body, verbose)
                resp = http_conn.getresponse()
                if resp.status == 200:
                    #resp.read(
                    self.verbose = verbose
                    return self.parse_response(resp)
            
            except xmlrpc_client.Fault:
                raise
            except Exception:
                #All unexpected errors leave connection in
                # a strange state, so we clear it.
                self.close() 
                raise
elif sys.version_info[0] == 2:
    class OurTransport(object, xmlrpc_client.Transport):
        def send_request(self, connection, handler, request_body):
            return super(OurTransport, self).send_request(connection, handler, request_body)

        def send_host(self, connection, host):
            return super(OurTransport, self).send_host(connection, host)

        def request(self, host, handler, request_body, verbose=1):
            # issue XML-RPC request

            h = self.make_connection(host)
            if verbose:
                h.set_debuglevel(1)

            self.send_request(h, handler, request_body)
            self.send_host(h, host)
            self.send_user_agent(h)
            self.send_content(h, request_body)

            errcode, errmsg, headers = h.getreply()

            if errcode != 200:
                sublime.error_message('Error connecting: ' + str(errcode) + ' ' + errmsg)
                
                raise xmlrpc_client.ProtocolError(
                    host + handler,
                    errcode, errmsg,
                    headers
                    )

            self.verbose = verbose

            try:
                sock = h._conn.sock
            except AttributeError:
                sock = None

            resp = self._parse_response(h.getfile(), sock)
            #pprint.pprint(resp)
            return resp

        def getparser(self, use_datetime=0):
            if use_datetime and not datetime:
                raise ValueError("the datetime module is not available")

            
            target = sublUnmarshaller(use_datetime=use_datetime)
            parser = xmlrpc_client.ExpatParser(target) 

            return parser, target

        def make_connection(self, host):
            # create a HTTP connection object from a host descriptor
            #import httplib
            host, extra_headers, x509 = self.get_host_info(host)
            return http_client.HTTP(host)

        def single_request(self, host, handler, request_body):
            # issue XML-RPC request
            try:
                http_conn = self.send_request(host, handler, request_body)
                resp = http_conn.getresponse()
                if resp.status == 200:
                    #resp.read()
                    self.verbose = verbose
                    return self.parse_response(resp)
            
            except xmlrpc_client.Fault:
                raise
            except Exception:
                #All unexpected errors leave connection in
                # a strange state, so we clear it.
                self.close() 
                raise

class Client(object):
    """
    Connection to a WordPress XML-RPC API endpoint.

    To execute XML-RPC methods, pass an instance of an
    `XmlrpcMethod`-derived class to `Client`'s `call` method.
    """

    def __init__(self, url, username, password, blog_id=0):
        self.url = url
        self.username = username
        self.password = password
        self.blog_id = blog_id
    
        try:
            self.transport = OurTransport()
            self.server = xmlrpc_client.ServerProxy(url, transport=self.transport, allow_none=True, verbose=False)
            self.supported_methods = self.server.mt.supportedMethods()
        except xmlrpc_client.ProtocolError:
            e = sys.exc_info()[1]
            sublime.error_message('Server connection error.')
            raise ServerConnectionError(repr(e))

    def call(self, method):
        if method.method_name not in self.supported_methods:
            sublime.error_message('Unsupported XMLRPC method: ' + method.method_name)
            raise UnsupportedXmlrpcMethodError(method.method_name)

        server_method = getattr(self.server, method.method_name)
        args = method.get_args(self)

        try:
            raw_result = server_method(*args)
        except xmlrpc_client.Fault:
            e = sys.exc_info()[1]
            if e.faultCode == 403:
                sublime.error_message('Invalid credentials.')
                raise InvalidCredentialsError(e.faultString)
            elif e.faultCode == 405:
                sublime.error_message('XMLRPC disabled on this host.')
                raise XmlrpcDisabledError(e.faultString)
            else:
                raise
        return method.process_result(raw_result)


class XmlrpcMethod(object):
    """
    Base class for XML-RPC methods.

    Child classes can override methods and properties to customize behavior:

    Properties:
        * `method_name`: XML-RPC method name (e.g., 'wp.getUserInfo')
        * `method_args`: Tuple of method-specific required parameters
        * `optional_args`: Tuple of method-specific optional parameters
        * `results_class`: Python class which will convert an XML-RPC response dict into an object
    """
    method_name = None
    method_args = tuple()
    optional_args = tuple()
    results_class = None

    def __init__(self, *args, **kwargs):
        if self.method_args or self.optional_args:
            if self.optional_args:
                max_num_args = len(self.method_args) + len(self.optional_args)
                if not (len(self.method_args) <= len(args) <= max_num_args):
                    raise ValueError("Invalid number of parameters to %s" % self.method_name)
            else:
                if len(args) != len(self.method_args):
                    raise ValueError("Invalid number of parameters to %s" % self.method_name)

            for i, arg_name in enumerate(self.method_args):
                setattr(self, arg_name, args[i])

            if self.optional_args:
                for i, arg_name in enumerate(self.optional_args, start=len(self.method_args)):
                    if i >= len(args):
                        break
                    setattr(self, arg_name, args[i])

        if 'results_class' in kwargs:
            self.results_class = kwargs['results_class']

    def default_args(self, client):
        """
        Builds set of method-non-specific arguments.
        """
        return tuple()

    def get_args(self, client):
        """
        Builds final set of XML-RPC method arguments based on
        the method's arguments, any default arguments, and their
        defined respective ordering.
        """
        default_args = self.default_args(client)

        if self.method_args or self.optional_args:
            optional_args = getattr(self, 'optional_args', tuple())
            args = []
            for arg in (self.method_args + optional_args):
                if hasattr(self, arg):
                    obj = getattr(self, arg)
                    if hasattr(obj, 'struct'):
                        args.append(obj.struct)
                    else:
                        args.append(obj)
            args = list(default_args) + args
        else:
            args = default_args

        return args

    def process_result(self, raw_result):
        """
        Performs actions on the raw result from the XML-RPC response.

        If a `results_class` is defined, the response will be converted
        into one or more object instances of that class.
        """
        if self.results_class and raw_result:
            if isinstance(raw_result, dict_type):
                return self.results_class(raw_result)
            elif isinstance(raw_result, collections.Iterable):
                return [self.results_class(result) for result in raw_result]

        return raw_result


class AnonymousMethod(XmlrpcMethod):
    """
    An XML-RPC method for which no authentication is required.
    """
    pass
class AuthenticatedMethod(XmlrpcMethod):
    """
    An XML-RPC method for which user authentication is required.
    Blog ID, username and password details will be passed from
    the `Client` instance to the method call.
    """
    def default_args(self, client):
        return (client.blog_id, client.username, client.password)