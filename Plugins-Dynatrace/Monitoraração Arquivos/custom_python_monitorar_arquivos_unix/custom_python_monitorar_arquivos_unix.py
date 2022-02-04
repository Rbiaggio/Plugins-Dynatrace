#!/usr/bin/env python3
import logging
from datetime import date, datetime, timedelta, timezone
import paramiko
from ruxit.api.base_plugin import RemoteBasePlugin
from workadays import workdays as wd

logger = logging.getLogger(__name__)
currentDate = date.today()
currentYear = currentDate.year
currentMonth = currentDate.month
currentDay = currentDate.day
br_timezone = timedelta(hours=-3)
currentTime = datetime.now(timezone(br_timezone)).strftime('%H:%M')
print('current date', currentDate)
print('current year', currentYear)
print('current month', currentMonth)
print('current day', currentDay)
print('current time', currentTime)

def getFirstDayOfMonth(date) -> datetime:
    firstDay = datetime(date.year, date.month, 1)
    return firstDay

def getLastDayOfMonth(date: date):
    lastDay = datetime(date.year + int(date.month / 12),
                       date.month % 12 + 1, 1) - timedelta(days=1)
    return lastDay

def isBetweenTime(start: str, end: str) -> bool:
    if (currentTime > start) and (currentTime < end):
        return True
    else:
        return False

def isHoliday(date) -> bool:
    holiday = wd.is_holiday(date, country='BR', years=date.year)
    return holiday

def isWeekend(date) -> bool:
    weekend = wd.is_weekend(date)
    return weekend


def isBetweenDays(date) -> bool:
    try:
        weekday = date.weekday()
        if (weekday >= 1) and (weekday <= 5):
            return True
        else:
            return False
    except Exception as e:
        return e


def isWorkDay(date) -> bool:
    if isHoliday(date) or isWeekend(date):
        return False
    else:
        return True


def isFirstWorkDayOfMonth(date) -> bool:
    firstDay = getFirstDayOfMonth(date)
    if (isWorkDay(date) and firstDay == date):
        return True
    else:
        return False


def isLastWorkDayOfMonthPlusOne(date) -> bool:
    lastDay = getLastDayOfMonth(date)
    nextDay = lastDay + timedelta(days=1)
    if (nextDay == currentDate):
        return True
    else:
        return False


class MonitorarArquivosUnix(RemoteBasePlugin):
    def query(self, **kwargs):
        config = kwargs['config']
        server = config['nome']
        ip = config['host_ip']
        port = config['host_port']
        path = config['path_file']
        file = config['file']
        user = config['host_username']
        pwd = config['host_password']
        beginning = config['start_time']
        end = config['finish_time']
        status_ok = "OK"
        status_notok = "Bad"
        var_cmd_output = 0
        br_timezone = timedelta(hours=-3)
        currentTime = datetime.now(timezone(br_timezone)).strftime('%H:%M')
        currentDay = currentDate.day
        if server == 'Arquivos Conductor (Baixa)' or server == 'Arquivos Conductor (Cad)' or server == 'Arquivos Conductor (Carga)' or server == 'Arquivos Conductor (Fin)' or server == 'Arquivos Conductor (Pag)':
            if isBetweenTime(beginning, end) and isBetweenDays(currentDate):
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(
                        paramiko.AutoAddPolicy())
                    client.connect(ip, username=user, password=pwd)
                    cmd = f'ls {path}/{file} | wc -l'
                    stdin, stdout, stderr = client.exec_command(cmd)
                    cmd_output = stdout.read()
                    var_cmd_output = int(cmd_output)
                    if var_cmd_output == 0:
                        state_return = status_notok
                        print("Status Arquivos Conductor", state_return)
                        print("Qtde Arquivos Conductor", var_cmd_output)
                        print("Horário Arquivos Conductor", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    else:
                        state_return = status_ok
                        print("Status Arquivos Conductor", state_return)
                        print("Qtde Arquivos Conductor", var_cmd_output)
                        print("Horário Arquivos Conductor", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    group = self.topology_builder.create_group(
                        "Monitoração Arquivos", "Monitoração Arquivos")
                    device = group.create_element(server, server)
                    device.add_endpoint(ip=ip, port=port)
                    # device.relative(key='var_cmd_output_relative', value=var_cmd_output_relative)
                    group.absolute(key='var_cmd_output', value=var_cmd_output)
                    device.state_metric(key='state_return', value=state_return)
                    client.close()
                except Exception as e:
                    logger.error(f'Exception | Exception final é: {e}')
            else:
                logger.info(f'Fora da janela de execução')
        if server == 'Conductor (CDT)':
            if isFirstWorkDayOfMonth(currentDate) and currentTime < '10:00':
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(
                        paramiko.AutoAddPolicy())
                    client.connect(ip, username=user, password=pwd)
                    cmd = f'ls {path}/{file} | wc -l'
                    stdin, stdout, stderr = client.exec_command(cmd)
                    cmd_output = stdout.read()
                    var_cmd_output = int(cmd_output)
                    if var_cmd_output == 0:
                        state_return = status_notok
                        print("Status Conductor CDT", state_return)
                        print("Qtde Arquivos Conductor CDT", var_cmd_output)
                        print("Horário Arquivos Conductor CDT", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    else:
                        state_return = status_ok
                        print("Status Conductor CDT", state_return)
                        print("Qtde Arquivos Conductor CDT", var_cmd_output)
                        print("Horário Arquivos Conductor CDT", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    group = self.topology_builder.create_group(
                        "Monitoração Arquivos", "Monitoração Arquivos")
                    device = group.create_element(server, server)
                    device.add_endpoint(ip=ip, port=port)
                    # device.relative(key='var_cmd_output_relative', value=var_cmd_output_relative)
                    group.absolute(key='var_cmd_output', value=var_cmd_output)
                    device.state_metric(key='state_return', value=state_return)
                    client.close()
                except Exception as e:
                    logger.error(f'Exception | Exception final é: {e}')
            else:
                logger.info(f'Fora da janela de execução')
        if server == 'SUST-FUNCAO':
            if isFirstWorkDayOfMonth(currentDate) and currentTime < '11:00':
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(
                        paramiko.AutoAddPolicy())
                    client.connect(ip, username=user, password=pwd)
                    cmd = f'ls {path}/{file} | wc -l'
                    stdin, stdout, stderr = client.exec_command(cmd)
                    cmd_output = stdout.read()
                    var_cmd_output = int(cmd_output)
                    if var_cmd_output == 0:
                        state_return = status_notok
                        print("Status Arquivos SUST-FUNCAO", state_return)
                        print("Qtde Arquivos SUST-FUNCAO", var_cmd_output)
                        print("Horário Arquivos SUST-FUNCAO", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    else:
                        state_return = status_ok
                        print("Status Arquivos SUST-FUNCAO", state_return)
                        print("Qtde Arquivos SUST-FUNCAO", var_cmd_output)
                        print("Horário Arquivos SUST-FUNCAO", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    group = self.topology_builder.create_group(
                        "Monitoração Arquivos", "Monitoração Arquivos")
                    device = group.create_element(server, server)
                    device.add_endpoint(ip=ip, port=port)
                    # device.relative(key='var_cmd_output_relative', value=var_cmd_output_relative)
                    group.absolute(key='var_cmd_output', value=var_cmd_output)
                    device.state_metric(key='state_return', value=state_return)
                    client.close()
                except Exception as e:
                    logger.error(f'Exception | Exception final é: {e}')
            else:
                logger.info(f'Fora da janela de execução')
        if server == 'SUST-NPE':
            if isLastWorkDayOfMonthPlusOne(currentDate) and currentTime < '06:00':
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(
                        paramiko.AutoAddPolicy())
                    client.connect(ip, username=user, password=pwd)
                    cmd = f'ls {path}/{file} | wc -l'
                    stdin, stdout, stderr = client.exec_command(cmd)
                    cmd_output = stdout.read()
                    var_cmd_output = int(cmd_output)
                    if var_cmd_output == 0:
                        state_return = status_notok
                        print("Status Arquivos SUST-NPE", state_return)
                        print("Qtde Arquivos SUST-NPE", var_cmd_output)
                        print("Horário Arquivos SUST-NPE", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    else:
                        state_return = status_ok
                        print("Status Arquivos SUST-NPE", state_return)
                        print("Qtde Arquivos SUST-NPE", var_cmd_output)
                        print("Horário Arquivos SUST-NPE", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    group = self.topology_builder.create_group(
                        "Monitoração Arquivos", "Monitoração Arquivos")
                    device = group.create_element(server, server)
                    device.add_endpoint(ip=ip, port=port)
                    # device.relative(key='var_cmd_output_relative', value=var_cmd_output_relative)
                    group.absolute(key='var_cmd_output', value=var_cmd_output)
                    device.state_metric(key='state_return', value=state_return)
                    client.close()

                except Exception as e:
                    logger.error(f'Exception | Exception final é: {e}')
            else:
                logger.info(f'Fora da janela de execução')
        if server == 'Matera (Clientes)' or server == 'Matera (Operacao)' or server == 'Matera (Baixa)' or server == 'Marera (Vencimento)' or server == 'Matera (InfoComplementar)':
            if isFirstWorkDayOfMonth(currentDate) and currentTime < '14:00':
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(
                        paramiko.AutoAddPolicy())
                    client.connect(ip, username=user, password=pwd)
                    cmd = f'ls {path}/{file} | wc -l'
                    stdin, stdout, stderr = client.exec_command(cmd)
                    cmd_output = stdout.read()
                    var_cmd_output = int(cmd_output)
                    if var_cmd_output == 0:
                        state_return = status_notok
                        print("Status Arquivos Matera", state_return)
                        print("Qtde Arquivos Matera", var_cmd_output)
                        print("Horário Arquivos Matera", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    else:
                        state_return = status_ok
                        print("Status Arquivos Matera", state_return)
                        print("Qtde Arquivos Matera", var_cmd_output)
                        print("Horário Arquivos Matera", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    group = self.topology_builder.create_group(
                        "Monitoração Arquivos", "Monitoração Arquivos")
                    device = group.create_element(server, server)
                    device.add_endpoint(ip=ip, port=port)
                    # device.relative(key='var_cmd_output_relative', value=var_cmd_output_relative)
                    group.absolute(key='var_cmd_output', value=var_cmd_output)
                    device.state_metric(key='state_return', value=state_return)
                    client.close()
                except Exception as e:
                    logger.error(f'Exception | Exception final é: {e}')
            else:
                logger.info(f'Fora da janela de execução')
        if server == 'Registro Boleto (Conn)' or server == 'Registros Boletos (MV)' or server == 'Registros Boletos (CB)':
            if isBetweenTime(beginning, end):
                try:
                    client = paramiko.SSHClient()
                    client.set_missing_host_key_policy(
                        paramiko.AutoAddPolicy())
                    client.connect(ip, username=user, password=pwd)
                    cmd = f'ls {path}/{file} | wc -l'
                    stdin, stdout, stderr = client.exec_command(cmd)
                    cmd_output = stdout.read()
                    var_cmd_output = int(cmd_output)
                    if var_cmd_output == 1:
                        state_return = status_notok
                        print("Status Boletos", state_return)
                        print("Qtde Arquivos Boletos", var_cmd_output)
                        print("Horário Arquivos Boletos", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    else:
                        state_return = status_ok
                        print("Status Boletos", state_return)
                        print("Qtde Arquivos Boletos", var_cmd_output)
                        print("Horário Arquivos Boletos", currentTime)
                        print("CurrentDay", currentDay)
                        print("CurrentDate", currentDate)
                    group = self.topology_builder.create_group(
                        "Monitoração Arquivos", "Monitoração Arquivos")
                    device = group.create_element(server, server)
                    device.add_endpoint(ip=ip, port=port)
                    # device.relative(key='var_cmd_output_relative', value=var_cmd_output_relative)
                    group.absolute(key='var_cmd_output', value=var_cmd_output)
                    device.state_metric(key='state_return', value=state_return)
                    client.close()
                except Exception as e:
                    logger.error(f'Exception | Exception final é: {e}')
            else:
                logger.info(f'Fora da janela de execução')
