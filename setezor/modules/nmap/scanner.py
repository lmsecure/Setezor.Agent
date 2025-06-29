import xmltodict
import json
import re
from datetime import datetime
from setezor.tools.shell_tools import create_shell_subprocess, create_async_shell_subprocess


class NmapScanner:
    '''
    Класс-обертка над утилитой nmap
    '''
    
    def __init__(self, task = None):
        self.task = task

    start_command = ['nmap', '--privileged', '-oX', '-']
    superuser_permision = ['sudo', '-S']
    
    def run(self, extra_args: str, _password: str, logs_path: str=None) -> dict:
        """Синхронная реализация запуска nmap с заданными параметрами

        Args:
            extra_args (str): дополнительные параметры сканирования
            _password (str): пароль суперпользователя 

        Raises:
            NmapCommandError: _description_

        Returns:
            dict: логи nmap-а
        """
        args = self._prepare_args(extra_args=extra_args)
        # time1 = time()
        result, error = create_shell_subprocess(self.superuser_permision + args if _password else args).communicate(_password)
        # logger.debug('Finish sync nmap scan after %.2f seconds', time() - time1)
        return self._check_results(args=args, result=result, error=error, logs_path=logs_path)    
    
    def _prepare_args(self, extra_args: str):
        bad_symbols = set(";|&$>#")
        index_bad_symbol = next((i for i, c in enumerate(extra_args) if c in bad_symbols), -1)
        if index_bad_symbol != -1:
            raise ValueError("Invalid character in command")
        args = [i for i in self.start_command + extra_args.split(' ') if i]
        # logger.debug('Start async nmap scan with command "%s"', ' '.join(args))
        return args
    
    def _check_results(self, args: list, result: str, error: str):
        if isinstance(error, bytes):
            error = error.decode()
        if isinstance(result, bytes):
            result = result.decode()
        error = ''.join([line for line in error.splitlines() if not any(keyword in line for keyword in ['NSOCK', 
                                                                                                        'INFO', 
                                                                                                        'MAC', 
                                                                                                        'DEBUG', 
                                                                                                        'WARNING',
                                                                                                        'Operation not permitted',
                                                                                                        'Offending packet',
                                                                                                        'Omitting future',
                                                                                                        ])])
        if not error or re.match(r'^\[sudo\] password for [^\n]+?$', error):
            return result
        # logger.error('Nmap sync scan failed with error\n%s', error)
        raise Exception(error)
    
    async def async_run(self, extra_args: str, _password: str):
        """Асинхронная реализация запуска nmap с заданными параметрами

        Args:
            extra_args (str): дополнительные параметры сканирования
            _password (str): пароль суперпользователя 

        Raises:
            NmapCommandError: _description_

        Returns:
            dict: логи nmap-а
        """
        args = self._prepare_args(extra_args=extra_args)
        # time1 = time()
        subprocess = await create_async_shell_subprocess(self.superuser_permision + args if _password else args)
        if self.task:
            self.task.pid = subprocess.pid
        result, error = await subprocess.communicate(_password)
        return self._check_results(args=args, result=result, error=error)
        

    @staticmethod
    def parse_xml(input_xml: str) -> dict:
        """Метод преобразования xml-логов nmap в dict формат

        Args:
            input_xml (str): логи nmap-а в формате xml

        Raises:
            NmapParserError: _description_

        Returns:
            dict: логи nmap-а
        """        
        try:
            tag = '</nmaprun>'
            closed_tag = input_xml[-15:]
            if isinstance(closed_tag, bytes):
                tag = tag.encode()
            if tag not in closed_tag:
                input_xml += tag
            dict_xml = xmltodict.parse(input_xml)
            json_result = json.dumps(dict_xml).replace('@', '')
            # logger.debug('Parse input xml file with size "%s"', len(input_xml if isinstance(input_xml, bytes) else input_xml.encode()))
            return json.loads(json_result)
        except Exception:
            # logger.error('Failed parse xml file with error\n%s', traceback.format_exc())
            raise Exception('Error with parsing nmap xml-file')

    @staticmethod
    def save_source_data(path: str, scan_xml: str, command: str) -> bool:
        """Метод сохранения сырых xml-логов nmap-а

        Args:
            path (str): путь до папки сохранения
            scan_xml (str): логи nmap-а в формате xml
            command (str): команда сканирования. на основе нее формируется имя файла

        Raises:
            NmapSaverError: _description_

        Returns:
            bool: _description_
        """
        full_path = f'{path}/{datetime.now().strftime("%Y-%m-%d %H:%M:%S")} {command.replace("/", "_")}.xml'
        # logger.info('Save scan_data to file by path "%s"', full_path)
        try:
            with open(full_path, 'wb' if isinstance(scan_xml, bytes) else 'w') as f:
                f.write(scan_xml)
            return True
        except Exception:
            # logger.error('Failed save source scan to path "%s"', full_path, exc_info=True)
            raise Exception('Failed save source scan to path "%s"' % full_path)
