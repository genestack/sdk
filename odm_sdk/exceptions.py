from urllib.error import URLError

MASTER_BRANCH = 'https://github.com/genestack/python-client/archive/master.zip'
PYPI_PACKAGE = 'genestack-client'


class GenestackBaseException(Exception):
    """
    Base class for Genestack exceptions.

    Use it to catch all exceptions raised explicitly by Genestack Python Client.
    """
    pass


class GenestackException(GenestackBaseException):
    """
    Client-side  exception class.

    Raise its instances (instead of :py:class:`~exceptions.Exception`)
    if anything is wrong on client side.
    """
    pass


class GenestackServerException(GenestackException):
    """
    Server-side exception class.

    Raised when Genestack server returns an error response
    (error message generated by Genestack Java code, not an HTTP error).
    """

    def __init__(self, message, path, post_data, debug=False, stack_trace=None):
        """
        :param message: exception message
        :type message: str
        :param path: path after server URL of connection.
        :type path: str
        :param post_data: POST data (file or dict)
        :type debug: bool
        :param debug: flag if stack trace should be printed
        :param stack_trace: server stack trace
        :type stack_trace: str
        """
        message = (message.decode('utf-8', 'ignore')
                   if isinstance(message, bytes) else message)

        GenestackException.__init__(self, message, path, post_data, debug, stack_trace)
        self.message = message
        self.debug = debug
        self.stack_trace = stack_trace
        self.path = path
        self.post_data = post_data

    def __str__(self):
        if isinstance(self.post_data, dict):
            message = 'Got error "%s" at call of method "%s" of "%s"' % (
                self.message,
                self.post_data.get('method', '<unknown>'),
                self.path
            )
        else:
            # upload file
            message = 'Got error "%s" at call of "%s"' % (
                self.message,
                self.path
            )
        if self.stack_trace:
            if self.debug:
                message += '\nStacktrace from server is:\n%s' % self.stack_trace
            else:
                message += '\nEnable debug option to retrieve traceback'

        return message


class GenestackResponseError(GenestackBaseException, URLError):
    """
    Wrapper for HTTP response errors.

    Extends :py:class:`urllib2.URLError` for backward compatibility.
    """
    def __init__(self, reason):
        self.args = reason,
        self.reason = reason

    def __str__(self):
        return '<urlopen error %s>' % self.reason


class GenestackConnectionFailure(GenestackBaseException, URLError):
    """
    Wrapper for server connection failures.

    Extends :py:class:`urllib2.URLError` for backward compatibility.
    """
    def __init__(self, message):
        self.message = "<connection failed %s>" % message

    def __str__(self):
        return self.message


class GenestackAuthenticationException(GenestackException):
    """
    Exception thrown on an authentication error response from server.
    """
    pass


class GenestackVersionException(GenestackException):
    """
    Exception thrown if server requires a newer version on Python Client.
    """

    def __init__(self, current_version, required_version=None):
        """

        :param current_version: current version
        :type current_version: str
        :param required_version: minimum required version
        :type required_version: str
        """
        if not required_version:
            message = 'Cannot get required version from server.\n'

        super(GenestackVersionException, self).__init__(message)
