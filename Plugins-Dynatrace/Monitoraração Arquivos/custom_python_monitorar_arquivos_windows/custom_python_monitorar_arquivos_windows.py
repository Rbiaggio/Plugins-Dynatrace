#!/usr/bin/env python3
import base64
import logging
import socket
from datetime import datetime, timedelta, timezone
from os.path import isfile
import paramiko
import winrm
from ruxit.api.base_plugin import RemoteBasePlugin
from workadays import workdays as wd
logger = logging.getLogger(__name__)
currentDate = datetime.today()
currentYear = currentDate.year
currentMonth = currentDate.month
currentDay = currentDate.day
br_timezone = timedelta(hours=-3)
currentTime = datetime.now(timezone(br_timezone)).strftime('%H:%M')
url = 'http://localhost:14499/metrics/ingest'
def isHoliday(year) -> bool:
    holiday = wd.is_holiday(currentDate.date, country='BR', years=year)
    return holiday
def isWeekend(date=currentDate) -> bool:
    weekend = wd.is_weekend(date)
    return weekend
def isWorkDay() -> bool:
    if isHoliday(currentYear) or isWeekend():
        return False
    else:
        return True
def isBetweenTime(start: str, end: str) -> bool:
    if (currentTime > start) and (currentTime < end):
        return True
    else:
        return False
def isBetweenDays() -> bool:
    weekday = currentDate.weekday
    if (weekday >= 1) and (weekday <= 5):
        return True
    else:
        return False
def winConnect(host, user, pwd, cmd):
    try:
        session = winrm.Session(host, auth=(user, pwd))
        result = session.run_cmd(cmd, ['/all'])
        return result
    except Exception as e:
        return e
def unixConnect(host, user, pwd, cmd):
    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=user, password=pwd)
        stdin, stdout, stderr = client.exec_command(cmd)
        result = {
            stdin, stdout, stderr
        }
        client.close()
        return result
    except Exception as e:
        return e
def checkFile(path: str):
    if isfile(path):
        return True
    else:
        return False
class HasFilePlugin(RemoteBasePlugin):
    def query(self, **kwargs):
        global state_return
        config = kwargs['config']
        server = config['nome']
        system = config['system_type']
        ip = config['host_ip']
        port = config['host_port']
        path = config['path_file']
        user = config['host_username']
        pwd = config['host_password']
        beginning = config['start_time']
        end = config['finish_time']
        state_return = 0.0
        status_ok = "OK"
        status_notok = "Bad"
        if system == 'Windows':
            try:
                result = winConnect(ip, user, pwd, 'dir')
                logger.info(f'Connection - Result: {result}')
                if not result:
                    logger.info(f'Não conectou - Result: {result}')
                else:
                    logger.info(f'Check File: {path} on {ip}')
                    if server == 'Arquivos Conductor':
                        if isBetweenTime(beginning, end) and isBetweenDays():
                            hasfile = checkFile(path)
                            if hasfile == True:
                                state_return = status_ok
                                print("Hasfile:", hasfile)
                                print("Status Windows:", state_return)
                            else:
                                print("Hasfile:", hasfile)
                                state_return = status_notok
                                print("Status Windows:", state_return)
                        else:
                            logger.info(f'Out of range')
                    else:
                        if isBetweenTime(beginning, end):
                            hasfile = checkFile(path)
                            if hasfile == True:                                
                                state_return = status_ok
                                print("Hasfile:", hasfile)
                                print("Status Windows:", state_return)
                            else:
                                state_return = status_notok
                                print("Hasfile:", hasfile)
                                print("Status Windows:", state_return)
                        else:
                            logger.info(f'Out of range')
                group = self.topology_builder.create_group(
                    "Monitora Arquivos", "Monitora Arquivos")
                device = group.create_element(
                    "Arquivos CIP", "Arquivos CIP")
                group.report_property(key="Desenvolvedor",
                                      value="César Augusto Costa")
                group.report_property(
                    key="Monitoramento", value="Arquivos")
                group.report_property(
                    key="Descrição", value="Diretório de Monitoramento de arquivos")
                group.absolute(key='state_return', value=state_return)
                device.report_property(
                    key="Monitoramento", value="Arquivos")
                device.report_property(key="Technology", value="Python")
                device.add_endpoint(ip=ip, port=port)
                device.relative(key='state_return', value=state_return)
                device.state_metric(key='state_return', value=state_return)
            except Exception as e:
                logger.info(str(e))
        else:
            try:
                result = unixConnect(ip, user, pwd, 'ls')
                logger.info(f'Connection - Result: {result}')
                if not result:
                    logger.info(f'Não conectou - Result: {result}')
                else:
                    logger.info(f'Check File: {path} on {ip}')
                    if server == 'Arquivos Conductor':
                        if isBetweenTime(beginning, end) and isBetweenDays():
                            hasfile = checkFile(path)
                            if hasfile == True:
                                state_return = status_ok
                                print("Hasfile:", hasfile)
                                print("Status Unix:", state_return)
                            else:
                                state_return = status_notok
                                print("Hasfile:", hasfile)
                                print("Status Unix:", state_return)
                        else:
                            logger.info(f'Out of range')
                    else:
                        if isBetweenTime(beginning, end):
                            hasfile = checkFile(path)
                            if hasfile == True:
                                state_return = status_ok
                                print("Hasfile:", hasfile)
                                print("Status Unix:", state_return)
                            else:
                                state_return = status_notok
                                print("Hasfile:", hasfile)
                                print("Status Unix:", state_return)
                        else:
                            logger.info(f'Out of range')
                group = self.topology_builder.create_group(
                    "Monitora Arquivos", "Monitora Arquivos")
                device = group.create_element(
                    "Arquivos CIP", "Arquivos CIP")
                group.report_property(key="Desenvolvedor",
                                      value="César Augusto Costa")
                group.report_property(
                    key="Monitoramento", value="Arquivos")
                group.report_property(
                    key="Descrição", value="Diretório de Monitoramento de arquivos")
                group.absolute(key='state_return', value=state_return)
                device.report_property(
                    key="Monitoramento", value="Arquivos")
                device.report_property(key="Technology", value="Python")
                device.add_endpoint(ip=ip, port=port)
                device.relative(key='state_return', value=state_return)
                device.state_metric(key='state_return', value=state_return)
            except Exception as e:
                logger.info(str(e))