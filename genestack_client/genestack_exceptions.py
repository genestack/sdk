# -*- coding: utf-8 -*-
MASTER_BRANCH = 'https://github.com/genestack/python-client/archive/master.zip'
PYPI_PACKAGE = 'genestack-client'


class GenestackException(Exception):
    """
    This is the base Genestack exception class. It should be used instead of
    :py:class:`~exceptions.Exception` to raise exceptions if something goes wrong.
    """
    pass


class GenestackServerException(GenestackException):
    """
    Should be thrown when a server sends a response with an error message from Java code.
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
        message = message.encode('utf-8', 'ignore') if isinstance(message, unicode) else message

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


class GenestackAuthenticationException(GenestackException):
    """
    Should be thrown when a server sends an authentication error.
    """
    pass


class GenestackVersionException(GenestackException):
    """
    Exception thrown if old version of client is used.
    """

    def __init__(self, current_version, required_version=None):
        """

        :param current_version: current version
        :type current_version: distutils.version.StrictVersion
        :param required_version: minimum required version
        :type required_version: distutils.version.StrictVersion
        """
        if required_version:
            package = MASTER_BRANCH if required_version.prerelease else PYPI_PACKAGE
            message = (
                'Your Genestack Client version "{current_version}" is too old, '
                'at least "{required_version}" is required.\n'
                ).format(current_version=current_version, required_version=required_version)
        else:
            package = PYPI_PACKAGE
            message = 'Cannot get required version from server.\n'

        message += (
            'You can update client with the following command:\n'
            '    pip install {package} --upgrade'
            ).format(package=package)

        super(GenestackVersionException, self).__init__(message)
