#!python
# -*- coding: utf-8 -*-

from __future__ import print_function

import glob
import json
import os
import sys
import time
import urllib2
import xml.dom.minidom as minidom
import zipfile
from collections import OrderedDict, namedtuple
from textwrap import TextWrapper

from genestack_client import GenestackException, GenestackServerException
from genestack_client.genestack_shell import Command, GenestackShell
from genestack_client.utils import ask_confirmation, isatty

if sys.stdout.encoding is None:
    # wrap sys.stdout into a StreamWriter to allow writing unicode to pipe
    # (in that case Python 2 cannot determine encoding)
    import codecs
    import locale
    sys.stdout = codecs.getwriter(locale.getpreferredencoding())(sys.stdout)


def validate_application_id(app_id):
    if len(app_id.split('/')) != 2:
        sys.stderr.write('Invalid application ID: expected "{vendor}/{application}", but got "%s" instead\n' % app_id)
        return False
    return True

APPLICATION_ID = 'genestack/application-manager'


SCOPE_DICT = {
    'system': 'SYSTEM',
    'user': 'USER',
    'session': 'SESSION'
}
DEFAULT_SCOPE = 'user'

VISIBILITIES = ['group', 'organization', 'all']


class Info(Command):
    COMMAND = 'info'
    DESCRIPTION = "Display information about an application's JAR file."
    OFFLINE = True

    def update_parser(self, p):
        p.add_argument(
            '-f', '--with-filename', action='store_true',
            help='show file names for each JAR'
        )
        p.add_argument(
            '-F', '--no-filename', action='store_true',
            help='do not show file names'
        )
        p.add_argument(
            '--vendor', action='store_true',
            help='show only vendor for each JAR file'
        )
        p.add_argument(
            'files', metavar='<jar_file_or_folder>', nargs='+',
            help='file to upload or folder with single JAR file inside (recursively)'
        )

    def run(self):
        jar_files = [resolve_jar_file(f) for f in match_jar_globs(self.args.files)]
        return show_info(
            jar_files, self.args.vendor,
            self.args.with_filename, self.args.no_filename
        )


class Install(Command):
    COMMAND = 'install'
    DESCRIPTION = "Upload and install an application's JAR file to a Genestack instance."

    def update_parser(self, p):
        p.add_argument(
            '-f', '--force', action='store_true',
            default=False,
            help='Run installation without any prompts (use with caution)'
        )
        p.add_argument(
            '-o', '--override', action='store_true',
            help='overwrite old version of the applications with the new one'
        )
        p.add_argument(
            '-s', '--stable', action='store_true',
            help='mark installed applications as stable'
        )
        p.add_argument(
            '-S', '--scope', metavar='<scope>', choices=SCOPE_DICT.keys(),
            default=DEFAULT_SCOPE,
            help='scope in which application will be stable'
                 ' (default is \'%s\'): %s' %
                 (DEFAULT_SCOPE, ' | '.join(SCOPE_DICT.keys()))
        )
        p.add_argument(
            '-i', '--visibility', metavar='<visibility>',
            help='set initial visibility (use `-i organization` for setting organization visibility or '
                 '`-i <group_accession>` for group visibility)'
        )
        p.add_argument(
            '-n', '--no-wait', action='store_true', dest='no_wait',
            help="Don't wait until all installed applications will be completely loaded"
        )
        p.add_argument(
            'version', metavar='<version>',
            help='version of applications to upload'
        )
        p.add_argument(
            'files', metavar='<jar_file_or_folder>', nargs='+',
            help='file to upload or folder with single JAR file inside (recursively)'
        )

    def run(self):
        jar_files = [resolve_jar_file(f) for f in match_jar_globs(self.args.files)]
        if not jar_files:
            raise GenestackException('No JAR file was found')
        upload_file(
            self.connection.application(APPLICATION_ID),
            jar_files, self.args.version, self.args.override,
            self.args.stable, self.args.scope, self.args.force, self.args.visibility, self.args.no_wait
        )


class ListVersions(Command):
    COMMAND = 'versions'
    DESCRIPTION = 'Show information about available applications.'

    def update_parser(self, p):
        p.add_argument(
            '-s', action='store_true', dest='show_stable',
            help='display stable scopes in output (S: System, U: User, E: sEssion)'
        )
        p.add_argument(
            '-i', action="store_true", dest='show_visibilities',
            help='display visibility of each version'
        )
        p.add_argument(
            '-l', action="store_true", dest='show_loading_state',
            help='display loading state of application with specific version'
        )
        p.add_argument(
            '-r', action="store_true", dest='show_release_state',
            help='display release state of version'
        )
        p.add_argument(
            '-o', action='store_true', dest='show_owned',
            help='show only versions owned by current user'
        )
        p.add_argument(
            'app_id', metavar='<appId>',
            help='application identifier to show versions'
        )

    def run(self):
        app_id = self.args.app_id
        if not validate_application_id(app_id):
            return
        app_info = self.connection.application(APPLICATION_ID).invoke(
            'getApplicationVersionsInfo',
            app_id,
            self.args.show_owned
        )
        if not app_info:
            sys.stderr.write('No suitable versions found for "%s"\n' % app_id)
            return
        app_info = OrderedDict(sorted(app_info.items()))

        max_len = max(len(x) for x in app_info.keys())
        for item in app_info.items():
            version_name = item[0]
            version_details = item[1]
            output_string = ''
            if self.args.show_stable:
                output_string += '%s%s%s ' % (
                    'S' if 'SYSTEM' in version_details['stableScopes'] else '-',
                    'U' if 'USER' in version_details['stableScopes'] else '-',
                    'E' if 'SESSION' in version_details['stableScopes'] else '-'
                )
            output_string += '%-*s' % (max_len + 2, version_name)
            if self.args.show_loading_state:
                output_string += '%7s' % (version_details['loadingState'].lower())
            if self.args.show_release_state:
                output_string += '%15s' % ('released' if version_details['released'] else 'not released')
            if self.args.show_visibilities:
                levels = version_details['visibilityLevels']
                visibility = 'all: ' + ('+' if 'all' in levels else '-')
                visibility += ', owner\'s organization: ' + ('+' if 'organization' in levels else '-')
                visibility +=\
                    ', groups: ' + ('-' if 'group' not in levels else '\'' + ('\', \''.join(levels['group'])) + '\'')
                output_string += '    %s' % visibility
            print(output_string)


class Status(Command):
    COMMAND = 'status'
    DESCRIPTION = 'Shows loading status of application and additional loading info'

    def update_parser(self, p):
        p.add_argument(
            'version', metavar='<version>', help='application version'
        )
        p.add_argument(
            'app_id_list', metavar='<appId>', nargs='+',
            help='identifier of the application'
        )
        p.add_argument(
            '-s', '--state-only', action='store_true', dest='state_only',
            help='show only id and state, without error descriptions'
        )

    def run(self):
        app_ids = self.args.app_id_list
        if not all(map(validate_application_id, app_ids)):
            return
        version = self.args.version

        lines = []
        for app_id in app_ids:
            app_info = self.connection.application(APPLICATION_ID).invoke(
                'getApplicationDescriptor', app_id, version
            )
            lines.append('%s%9s' % (app_id, app_info['state'].lower()))
            if not self.args.state_only:
                lines.extend(format_loading_messages_by_lines(app_info.get('loadingErrors', []),
                                                              app_info.get('loadingWarnings', [])))
        print('\n'.join(lines))


class Visibility(Command):
    COMMAND = 'visibility'
    DESCRIPTION = 'Set or remove visibility for application'

    def update_parser(self, p):
        p.add_argument(
            '-r', '--remove', action='store_true', dest='remove',
            help='Specifies if visibility must be removed (by default specific visibility will be added)'
        )
        p.add_argument(
            'app_id', metavar='<appId>', help='application identifier'
        )
        p.add_argument(
            'version', metavar='<version>', help='application version'
        )
        p.add_argument(
            'level', metavar='<level>', choices=VISIBILITIES,
            help='Visibility level which will be set to application: %s' % (' | '.join(VISIBILITIES))
        )
        p.add_argument(
            'accessions', metavar='<groups_accessions>', nargs='*',
            help="Accessions of groups for 'group' visibility rule"
        )

    def run(self):
        change_applications_visibility(
            self.args.remove, self.connection.application(APPLICATION_ID), [self.args.app_id], self.args.version,
            self.args.level, self.args.accessions
        )


class Release(Command):
    COMMAND = 'release'
    DESCRIPTION = 'Create released application from testing one'

    def update_parser(self, p):
        p.add_argument(
            'app_id', metavar='<appId>', help='application identifier'
        )
        p.add_argument(
            'version', metavar='<version>', help='application version'
        )
        p.add_argument(
            'new_version', metavar='<newVersion>',
            help='version of released application (must differ from other version of this application)'
        )

    def run(self):
        release_applications(
            self.connection.application(APPLICATION_ID), [self.args.app_id], self.args.version, self.args.new_version
        )


class ListApplications(Command):
    COMMAND = 'applications'
    DESCRIPTION = 'Show information about available applications.'

    def run(self):
        result = self.connection.application(APPLICATION_ID).invoke('listApplications')
        result.sort()
        for item in result:
            print(item)


class MarkAsStable(Command):
    COMMAND = 'stable'
    DESCRIPTION = 'Mark applications with the specified version as stable.'

    def update_parser(self, p):
        p.add_argument(
            'version', metavar='<version>',
            help='applications version or \'-\' (hyphen) to remove'
                 ' stable version'
        )
        p.add_argument(
            'app_id_list', metavar='<appId>', nargs='+',
            help='ID of the application to be marked as stable'
        )
        p.add_argument(
            '-S', '--scope', metavar='<scope>', choices=SCOPE_DICT.keys(),
            default=DEFAULT_SCOPE,
            help='scope in which the application will be stable'
                 ' (default is \'%s\'): %s' %
                 (DEFAULT_SCOPE, ' | '.join(SCOPE_DICT.keys()))
        )

    def run(self):
        apps_ids = self.args.app_id_list
        if not all(map(validate_application_id, apps_ids)):
            return
        version = self.args.version
        if version == '-':
            version = None
        return mark_as_stable(
            self.connection.application(APPLICATION_ID), version, apps_ids,
            self.args.scope
        )


class Remove(Command):
    COMMAND = 'remove'
    DESCRIPTION = 'Remove a specific version of an application.'

    def update_parser(self, p):
        p.add_argument(
            '-f', '--force', action='store_true',
            default=False,
            help='Remove without any prompts (use with caution)'
        )
        p.add_argument(
            'version', metavar='<version>', help='application version'
        )
        p.add_argument(
            'app_id_list', metavar='<appId>', nargs='+',
            help='identifier of the application to remove'
                 ' (or `ALL` for removing all _your_ applications with specified version)'
        )

    def run(self):
        app_ids = self.args.app_id_list
        if app_ids == ['ALL']:
            app_ids = None
        elif not all(map(validate_application_id, app_ids)):
            return
        application = self.connection.application(APPLICATION_ID)
        version = self.args.version
        if not self.args.force and not prompt_removing_stable_version(application, app_ids, version):
            raise GenestackException('Removing was aborted by user')
        return remove_applications(
            self.connection.application(APPLICATION_ID), self.args.version, app_ids
        )


class Reload(Command):
    COMMAND = 'reload'
    DESCRIPTION = 'Reload a specific version of an application.'

    def update_parser(self, p):
        p.add_argument(
            'version', metavar='<version>', help='application version'
        )
        p.add_argument(
            'app_id_list', metavar='<appId>', nargs='+',
            help='ID of the application to be marked as stable'
        )

    def run(self):
        apps_ids = self.args.app_id_list
        if not all(map(validate_application_id, apps_ids)):
            return
        return reload_applications(
            self.connection.application(APPLICATION_ID), self.args.version, apps_ids
        )


# FIXME: This class should be removed; it is written only for debug purposes:
class Invoke(Command):
    COMMAND = 'invoke'
    DESCRIPTION = 'Invoke method of a stable application.'

    def update_parser(self, p):
        p.add_argument(
            'app_id', metavar='<appId>',
            help='application identifier'
        )
        p.add_argument(
            'method_name', metavar='<method>',
            help='application method to call'
        )
        p.add_argument(
            'arguments', metavar='<args>', nargs='*',
            help='application method to call'
        )

    def run(self):
        application = self.connection.application(self.args.app_id)
        args = []
        for arg in self.args.arguments:
            try:
                args.append(json.loads(arg))
            except ValueError:
                args.append(arg)
        response = application.invoke(self.args.method_name, *args)
        if isinstance(response, list):
            for item in response:
                print(item)
        else:
            print(response)


def match_jar_globs(paths):
    """ Return a list of files or directories by list of globs. """
    return sum([glob.glob(p) for p in paths], [])


def resolve_jar_file(file_path):
    if not os.path.exists(file_path):
        raise GenestackException("No such file or directory: %s" % file_path)
    if not os.path.isdir(file_path):
        return file_path

    jar_files = []
    for dirpath, dirnames, filenames in os.walk(file_path, followlinks=True):
        for f in filenames:
            if f.lower().endswith('.jar'):
                jar_files.append(os.path.join(dirpath, f))

    if len(jar_files) > 1:
        raise GenestackException('More than one JAR file was found inside %s:\n'
                                 ' %s' % (file_path, '\n '.join(jar_files)))
    elif not jar_files:
        raise GenestackException('No JAR files were found within given files/directories: "%s"' %
                                 file_path)

    return jar_files[0]


def mark_as_stable(application, version, app_id_list, scope):
    print('Setting the application version "%s" stable for scope %s' % (version, scope))
    scope = SCOPE_DICT[scope]
    for app_id in app_id_list:
        sys.stdout.write('%-40s ... ' % app_id)
        sys.stdout.flush()
        try:
            if scope == 'SYSTEM':  # For SYSTEM scope we must wait when application will be loaded
                if wait_application_loading(application, app_id, version).success:
                    application.invoke('markAsStable', app_id, scope, version)
                    sys.stdout.write('ok\n')
                    sys.stdout.flush()
            else:
                application.invoke('markAsStable', app_id, scope, version)
                sys.stdout.write('ok\n')
                sys.stdout.flush()
        except GenestackServerException as e:
            handle_server_error_gracefully(e)


def remove_applications(application, version, app_id_list):
    print('Removing application(s) with version "%s"' % version)
    if app_id_list:
        for app_id in app_id_list:
            sys.stdout.write('%-40s ... ' % app_id)
            sys.stdout.flush()
            try:
                application.invoke('removeApplication', app_id, version)
                sys.stdout.write('ok\n')
                sys.stdout.flush()
            except GenestackServerException as e:
                handle_server_error_gracefully(e)
    else:
        sys.stdout.write('ALL ... ')
        sys.stdout.flush()
        removed_apps = application.invoke('removeApplications', version)
        sys.stdout.write('ok\n')
        sys.stdout.flush()
        sys.stdout.write('Following applications were removed:\n %s\n' % ('\n '.join(sorted(removed_apps))))
        sys.stdout.flush()


def reload_applications(application, version, app_id_list):
    print('Reloading applications')
    for app_id in app_id_list:
        sys.stdout.write('%-40s ... ' % app_id)
        sys.stdout.flush()
        try:
            application.invoke('reloadApplication', app_id, version)
            sys.stdout.write('ok\n')
            sys.stdout.flush()
        except GenestackServerException as e:
            handle_server_error_gracefully(e)


def upload_file(application, files_list, version, override, stable, scope, force, initial_visibility, no_wait):
    for file_path in files_list:
        upload_single_file(
            application, file_path, version, override,
            stable, scope, force, initial_visibility, no_wait
        )


def upload_single_file(application, file_path, version, override,
                       stable, scope, force=False, initial_visibility=None, no_wait=False):
    app_info = read_jar_file(file_path)
    if not force and override and not (stable and SCOPE_DICT[scope] == 'SYSTEM'):
        if get_system_stable_apps_version(application, app_info.identifiers, version):
            raise GenestackException('Can\'t install version "%s". This version is already system stable.\n' % version +
                                     'If you want to upload a new version and make it stable, add "-S system" option.\n' +
                                     'Otherwise use another version name.')

    parameters = {'version': version, 'override': override}
    upload_token = application.invoke('getUploadToken', parameters)

    if upload_token is None:
        raise GenestackException('Received a null token, the upload is not accepted')

    # upload_token, as returned by json.load(), is a Unicode string.
    # Without the conversion, urllib2.py passes a Unicode URL created from it
    # to httplib.py, and httplib.py fails in a non-graceful way
    # (http://bugs.python.org/issue12398)
    upload_token = upload_token.encode('UTF-8', 'ignore')
    try:
        result = application.upload_file(file_path, upload_token)
        # hack before fix ApplicationManagerApplication#processReceivedFile // TODO: return some useful information
        if result:
            print(result)
    except urllib2.HTTPError as e:
        raise GenestackException('HTTP Error %s: %s\n' % (e.code, e.read()))

    if not no_wait:
        identifiers_number = len(app_info.identifiers)
        for i, app_id in enumerate(app_info.identifiers):
            success, descriptor = wait_application_loading(application, app_id, version)
            if i == identifiers_number - 1:
                errors = descriptor.get('loadingErrors', [])
                warns = descriptor.get('loadingWarnings', [])
                if errors or warns:
                    lines = ['Module was loaded with following errors and warnings:']
                    lines.extend(
                        format_loading_messages_by_lines(errors, warns)
                    )
                    print('\n'.join(lines))
    else:
        sys.stdout.write("Uploading was done with 'no_wait' flag. Loading errors and warnings can be viewed"
                         " with 'status' command.\n")
        sys.stdout.flush()

    if initial_visibility:
        change_applications_visibility(
            False, application, app_info.identifiers, version,
            'organization' if initial_visibility == 'organization' else 'group',
            None if initial_visibility == 'organization' else [initial_visibility]
        )

    if not stable:
        return

    return mark_as_stable(
        application,
        version,
        app_info.identifiers,
        scope
    )


def release_applications(application, app_ids, version, new_version):
    print('Releasing new version "%s"' % new_version)
    for app_id in app_ids:
        if not validate_application_id(app_id):
            sys.stderr.write('Invalid application id: %s\n' % app_id)
            continue
        sys.stdout.write('%-40s ... ' % app_id)
        sys.stdout.flush()
        if wait_application_loading(application, app_id, version).success:
            application.invoke('releaseApplication', app_id, version, new_version)
            sys.stdout.write('ok\n')
            sys.stdout.flush()


def change_applications_visibility(remove, application, app_ids, version, level, accessions=None):
    def invoke_change(group_accession=None):
        application.invoke(
            'removeVisibility' if remove else 'addVisibility',
            app_id, version, level, group_accession if group_accession else None
        )
    try:
        print('%s visibility "%s" for version "%s"' % ('Removing' if remove else 'Setting', level, version))
        for app_id in app_ids:
            if not validate_application_id(app_id):
                sys.stderr.write('Invalid application id: %s\n' % app_id)
                continue
            sys.stdout.write('%-40s ... ' % app_id)
            sys.stdout.flush()
            if accessions:
                for accession in accessions:
                    invoke_change(accession)
            else:
                invoke_change()
            sys.stdout.write('ok\n')
            sys.stdout.flush()
    except GenestackException as e:
        sys.stderr.write('%s\n' % e.message)
        return 1
    return


def get_application_descriptor(application, application_id, version):
    return application.invoke('getApplicationDescriptor', application_id, version)


def wait_application_loading(application, app_id, version, seconds=1):
    first = True
    while True:
        descriptor = get_application_descriptor(application, app_id, version)
        if descriptor['state'] == 'FAILED':
            sys.stdout.write('\nLoading of application %s failed\n' % app_id)
            return LoadingResult(False, descriptor)
        elif descriptor['state'] == 'LOADING' and first:
            sys.stdout.write('\nApplication %s is not loaded yet. Waiting for loading (interrupt to abort)... ' % app_id)
            sys.stdout.flush()
            first = False
        elif descriptor['state'] == 'LOADED':
            break
        time.sleep(seconds)
    return LoadingResult(True, descriptor)


def format_loading_messages_by_lines(errors, warnings):
    wrapper = TextWrapper(initial_indent='\t\t', subsequent_indent='\t\t', width=80)
    lines = []
    if warnings:
        lines.append('\t%s' % 'Warnings:')
        lines.append('\n\n'.join([wrapper.fill(warning) for warning in warnings]))
    if errors:
        lines.append('\t%s' % 'Errors:')
        lines.append('\n\n'.join([wrapper.fill(error) for error in errors]))
    return lines


AppInfo = namedtuple('AppInfo', [
    'vendor', 'identifiers'
])


LoadingResult = namedtuple('LoadingResult', [
    'success', 'descriptor'
])


def log_on_error(function):
    """
    Wrapper to print arguments to stderr on exception.

    :param function: function to decorate
    :return: decorated function
    """
    def wrapper(*args):
        try:
            return function(*args)
        except Exception:
            sys.stderr.write('Error at "%s" with arguments: %s\n' % (function.__name__, ', '.join(map(repr, args))))
            raise
    return wrapper


@log_on_error
def read_jar_file(file_path):
    with zipfile.ZipFile(file_path) as zip_file:
        try:
            info = zip_file.getinfo('applications.xml')
            with zip_file.open(info) as manifest:
                doc = minidom.parse(manifest)
                namespace = doc.documentElement.namespaceURI
                applications = doc.getElementsByTagNameNS(namespace, 'application')
                vendor = doc.getElementsByTagNameNS(namespace, 'vendor')[0].firstChild.nodeValue
                identifiers = [
                    vendor + '/' + a.getElementsByTagNameNS(namespace, 'id')[0].firstChild.nodeValue
                    for a in applications
                ]
        except KeyError as e:
            raise GenestackException('Unable to read applications.xml manifest from %s: %s' % (
                os.path.abspath(file_path), e))
        return AppInfo(vendor, identifiers)


def show_info(files, vendor_only, with_filename, no_filename):
    first_file = True
    for file_path in files:
        app_info = read_jar_file(file_path)

        if vendor_only:
            if no_filename:
                print(app_info.vendor)
            else:
                print('%s %s' % (file_path, app_info.vendor))
            continue

        if with_filename or not no_filename and len(files) > 1:
            if not first_file:
                print()
            print('File:', file_path)

        print('Vendor:', app_info.vendor)
        print('Applications:')
        for app_id in sorted(app_info.identifiers):
            print('\t%s' % app_id)

        first_file = False


REMOVE_PROMPT = '''You are going to remove following system stable applications with version "%s":
 %s
 '''


def prompt_removing_stable_version(application, apps_ids, version):
    check_tty()
    if apps_ids:
        apps = get_system_stable_apps_version(application, apps_ids, version)
    else:
        apps = application.invoke('getSystemStableIdsByVersion', version)

    if not apps:
        return True

    message = REMOVE_PROMPT % (version, '\n '.join(sorted(apps)))
    try:
        sys.stdout.write(message)
        sys.stdout.flush()
        return ask_confirmation('Do you want to continue')
    except KeyboardInterrupt:
        return False


def get_system_stable_apps_version(application, apps_ids, version):
    apps = []
    for app_id in apps_ids:
        stable_versions = application.invoke('getStableVersions', app_id)
        if stable_versions.get('SYSTEM') == version:
            apps.append(app_id)
    return apps


def check_tty():
    if not isatty():
        raise GenestackException("Prompt cannot be called")


def handle_server_error_gracefully(e):
    if e.debug:
        sys.stderr.write(str(e))
    else:
        sys.stdout.write("Error: %s (Enable debug option to retrieve traceback)\n" % e.message)
        sys.stdout.flush()


class ApplicationManager(GenestackShell):
    DESCRIPTION = ('The Genestack Application Manager is a command-line utility'
                   ' that allows you to upload and manage'
                   ' your applications on a specific Genestack instance ')
    INTRO = "Application manager shell.\nType 'help' for list of available commands.\n"
    COMMAND_LIST = [
        Info, Install, ListVersions, ListApplications, MarkAsStable, Remove, Reload, Invoke, Visibility, Release, Status
    ]


def main():
    shell = ApplicationManager()
    shell.cmdloop()

if __name__ == '__main__':
    main()
