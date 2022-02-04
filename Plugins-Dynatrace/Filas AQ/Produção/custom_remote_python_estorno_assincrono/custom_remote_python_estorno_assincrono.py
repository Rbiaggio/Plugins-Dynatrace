import logging
import cx_Oracle
import os
from ruxit.api.base_plugin import RemoteBasePlugin
import getpass
logger = logging.getLogger(__name__)

class EstornoAssincrono(RemoteBasePlugin):

    def query(self, **kwargs):

        global con, total_lancamentos_retorno_assincrono, state_retorno_assincrono

        state_retorno_assincrono = 0.0
        status_ok = "OK"
        status_notok = "Bad"

        try:
            con = cx_Oracle.connect(user="", password="", dsn="")
            cursor = con.cursor()
            print("Successfully connected to Oracle Database")
            consulta_sql = "select 'QCC_ESTO_ASSINCRONO' , count(1) from cc_qcc_esto_assincrono where state <> 3"
            cursor.execute(consulta_sql)
            resultado_query = (cursor.fetchall())

            for linha in resultado_query:
                total_lancamentos_retorno_assincrono = (linha[0])
                print("Total Registros", total_lancamentos_retorno_assincrono)

            if total_lancamentos_retorno_assincrono == 0:
                state_retorno_assincrono = status_ok
                print("Status:", state_retorno_assincrono)
            else:
                state_retorno_assincrono = status_notok
                print("Status:", state_retorno_assincrono)

            group = self.topology_builder.create_group("Filas AQ", "Filas AQ")
            device = group.create_element("Estorno Assincrono", "Estorno Assincrono")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="Oracle")
            group.report_property(key="Integrações", value="AWS")
            group.report_property(key="Descrição", value="Filas Oracle AQ - Conta e Standin")
            device.report_property(key="Integrações", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.add_endpoint(ip="10.26.27.175", port=3306, dnsNames=["HMATERA"])
            device.relative(key='total_lancamentos_retorno_assincrono', value=total_lancamentos_retorno_assincrono)
            group.absolute(key='total_lancamentos_retorno_assincrono', value=total_lancamentos_retorno_assincrono)
            device.state_metric(key='state_retorno_assincrono', value=state_retorno_assincrono)

        except cx_Oracle.DatabaseError as e:
            print("Erro ao acessar tabela", e)

        finally:
            print("Conexão ao banco encerrada")