"""Contains wp-cli calling and parsing classes / methods"""
import os
import getpass
import subprocess
import json
from random import randint
from logmod import Log
from datetime import datetime
L = Log()

class Installations(object):
    """Class used for obtaining installation dir and details"""
    def __init__(self, app):
        self.app = app
        L.debug('Installations Initialized')
        self.call = Call()
        self.username = getpass.getuser()
        self.homedir = os.path.expanduser('~%s' % self.username)
        self.app.state.homedir = self.homedir
        L.debug("Homedir: %s", self.homedir)
        self.installations = self.get_installation_dirs()
        if self.installations:
            self.get_installation_details()
            L.debug("WP Installation for user %s: %s", self.username, self.installations)
        else:
            L.warning("No WP Installations available for this User!")
    def get_installation_dirs(self):
        """Gets installation directory list using os.walk"""
        installations = []
        L.debug("%s Homedir: %s", self.username, self.homedir)
        for root, _, files in os.walk(self.homedir, topdown=True):
            if 'wp-config.php' in files:
                if not '/.' in root:
                    _x = {
                        'directory' : root,
                        'home_url' : '',
                        'valid_wp_options' : False,
                        'wp_db_check_success' : False,
                        'wp_db_error' : ''
                    }
                    installations.append(_x)
        return installations
    def get_installation_details(self):
        """Getter for installation details"""
        L.debug('Start get_installation_details')
        self.progress = 0
        if self.installations:
            progress_sections = 100 / len(self.installations)
        else:
            progress_sections = 100
        progress_increments = progress_sections / 2
        for installation in self.installations:
            self.progress = self.progress + progress_increments
            #L.debug('Progress: %s', self.progress)
            os.write(self.app.action_pipe, str(self.progress))
            db_check_data, db_check_error = self.call.wpcli(
                installation['directory'],
                ['db', 'check'])
            if db_check_data:
                data = db_check_data.splitlines()
                for line in data:
                    if '_options' in line and 'OK' in line:
                        #L.debug('Line: %s', line)
                        installation['valid_wp_options'] = True
                        self.progress = self.progress + progress_increments
                        #L.debug('Progress: %s', self.progress)
                        os.write(self.app.action_pipe, str(self.progress))
                        homedata, _ = self.call.wpcli(
                            installation['directory'],
                            ['option', 'get', 'home', '--skip-plugins', '--skip-themes'])
                        if homedata:
                            installation['home_url'] = homedata.rstrip()
                    if 'Success: Database checked' in line:
                        installation['wp_db_check_success'] = True
            if db_check_error:
                installation['wp_db_error'] = db_check_error
        os.close(self.app.action_pipe)
class DatabaseInformation(object):
    """Obtains database information"""
    def __init__(self, app):
        self.app = app
        L.debug('Installations Initialized')
        self.call = Call()
        self.installation = self.app.state.active_installation
        self.db_info = {
            'name': None,
            'size': None,
            'size_error': None,
            'check_tables': None,
            'check_error': None
        }
        self.get_db_size()
    def get_db_size(self):
        """Get database size and name list"""
        path = self.installation['directory']
        self.progress = 0
        progress_increments = 100 / 2

        #GET DATABASE NAME AND SIZE
        self.progress = self.progress + progress_increments
        L.debug('Progress: %s', self.progress)
        os.write(self.app.action_pipe, str(self.progress))
        dbsize_result, dbsize_error = self.call.wpcli(
            path, [
                'db', 'size',
                '--human-readable',
                '--format=json', '--no-color'])
        if dbsize_result:
            result_json = json.loads(dbsize_result)
            L.debug(
                'wp_db_name: %s, wp_db_size:%s',
                result_json[0]['Name'],
                result_json[0]['Size'])
            self.db_info['name'] = result_json[0]['Name']
            self.db_info['size'] = result_json[0]['Size']
        if dbsize_error:
            L.debug('wp_db_size error:%s', dbsize_error.decode(encoding='UTF-8'))
            self.db_info['size_error'] = dbsize_error.decode(encoding='UTF-8')
        #RUN CHECK DB
        self.progress = self.progress + progress_increments
        L.debug('Progress: %s', self.progress)
        os.write(self.app.action_pipe, str(self.progress))
        if dbsize_result:
            dbcheck_result, dbcheck_error = self.call.wpcli(path, ['db', 'check'])
            dbcheck_result_list = []
            if dbcheck_result:
                for line in dbcheck_result.splitlines():
                    if self.db_info['name'] in line:
                        _x = line.split()
                        dbcheck_result_list.append(
                            {
                                'table_name': _x[0],
                                'check_status': _x[1]
                            }
                        )
                self.db_info['check_tables'] = dbcheck_result_list
            if  dbcheck_error:
                self.db_info['check_error'] = dbcheck_error.decode(encoding='UTF-8')
        #L.debug('db_info: %s',self.db_info)
        os.close(self.app.action_pipe)
    def export(self):
        """Exports wp database"""
        install_path = self.installation['directory']
        n_length = 6
        rand_numb = ''.join(
            [
                "%s" % randint(0, 9) for _ in range(0, n_length)
            ])
        date = datetime.now()
        date = datetime.strftime(
            date,
            "%Y%m%d")
        file_name = self.db_info['name'] + \
            '-' + date  + '-' + rand_numb + '.sql'
        file_path = os.path.join(
            install_path,
            file_name)
        export = self.call.wpcli(
            install_path,
            [
                'db',
                'export',
                file_path
            ])
        if export[0]:
            L.debug('Export Result:  %s', export[0])
            return export[0]
        return "Database Export Failed"
    def import_db(self, path):
        """Exports wp database"""
        install_path = self.installation['directory']
        file_path = path
        import_result = self.call.wpcli(
            install_path,
            [
                'db',
                'import',
                file_path
            ])
        L.debug('Import_results: %s', import_result)
        if import_result[0]:
            L.debug('Import Result:  %s', import_result[0])
            return import_result[0]
        return "Database Export Failed"
    def get_import_list(self):
        """Return list of imports in user's directory"""
        imports = []
        username = getpass.getuser()
        homedir = os.path.expanduser('~%s' % username)
        L.debug("%s Homedir: %s", username, homedir)
        db_name = self.db_info['name']
        L.debug('db_name: %s', db_name)
        for root, _, files in os.walk(homedir, topdown=True):
            for file_name  in files:
                if db_name in file_name:
                    L.debug('Import Found: %s', file_name)
                    if not '/.' in root:
                        _x = os.path.join(root, file_name)
                        imports.append(_x)
        return imports
class WpConfig(object):
    """Obtains and modified wp_config information"""
    def __init__(self, app):
        self.app = app
        L.debug('Installations Initialized')
        self.call = Call()
        self.installation = self.app.state.active_installation
        self.wp_config_directive_list = []
        self.wp_config_error = None
        self.progress = 0
        #self.get_wp_config()
    def get_wp_config(self):
        """getter for wp_config data"""
        path = self.app.state.active_installation['directory']
        self.progress = 0
        progress_increments = 100
        self.progress = self.progress + progress_increments
        L.debug('Progress: %s', self.progress)
        os.write(self.app.action_pipe, str(self.progress))
        wp_config_result, wp_config_error = self.call.wpcli(
            path, [
                'config', 'list',
                '--format=json',
                '--no-color'])
        if wp_config_result:
            #L.debug('wp_config_result: %s', wp_config_result)
            self.wp_config_directive_list = json.loads(wp_config_result)
        if  wp_config_error:
            L.debug('wp_config_error: %s', wp_config_result)
            self.wp_config_error = wp_config_error
        os.close(self.app.action_pipe)
    def set_wp_config(self, directive_name, directive_value):
        """Sets a single wp_config directive.
        This is used by the wp_config display screen edit widgets"""
        path = self.app.state.active_installation['directory']
        return_data, return_error = self.call.wpcli(
            path, [
                'config',
                'set',
                directive_name,
                directive_value])
        L.debug('Set_Wp_Config Return Data: %s, Return Error: %s', return_data, return_error)
        if return_data and 'Success' in return_data:
            return True
        else:
            return False
    def del_wp_config(self, directive_name):
        """Sets a single wp_config directive.
        This is used by the wp_config display screen edit widgets"""
        path = self.app.state.active_installation['directory']
        return_data, return_error = self.call.wpcli(
            path, [
                'config',
                'delete',
                directive_name
                ])
        L.debug('Set_Wp_Config Return Data: %s, Return Error: %s', return_data, return_error)
        if return_data and 'Success' in return_data:
            return True
        else:
            return False
    def re_salt(self):
        "Refreshes the stalts defined in the wp-config.php file"
        path = self.app.state.active_installation['directory']
        return_data, return_error = self.call.wpcli(
            path, [
                'config',
                'shuffle-salts'
                ])
        L.debug('Set_Wp_Config Return Data: %s, Return Error: %s', return_data, return_error)
class Call(object):
    """opens a subprocess to run wp-cli command"""
    def wpcli(self, path, arguments):
        """runs_wp-cli command"""
        popen_args = ['wp']
        for argument in arguments:
            popen_args.append(argument)
        popen_args.append('--path='+path)

        data, error = subprocess.Popen(
            popen_args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
            ).communicate()
        return data, error
