Calling methods
***************

To call application method you need to know application_id and method name::

    from genestack import get_connection


    connection = get_connection()
    print connection.application('genestack/signin').invoke('whoami')


If your application have a lot of methods you may create own class::

    from genestack import Application, get_connection


    class SignIn(Application):
        APPLICATION_ID = 'genestack/signin'

        def whoami(self):
            return self.invoke('whoami')


    connection = get_connection()
    signin = SignIn(connection)
    print signin.whoami()

Calling method with arguments::

    from genestack import get_connection, Metainfo, PRIVATE


    connection = get_connection()
    metainfo = Metainfo()
    metainfo.add_string(Metainfo.NAME, "New folder")
    print connection.application('genestack/filesUtil').invoke('createFolder', PRIVATE, metainfo)

Number, order and type of arguments should match for python and java method.