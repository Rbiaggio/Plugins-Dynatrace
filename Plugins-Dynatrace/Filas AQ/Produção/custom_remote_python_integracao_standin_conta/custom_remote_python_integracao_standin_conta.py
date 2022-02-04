import logging
import cx_Oracle
import os
from ruxit.api.base_plugin import RemoteBasePlugin
import getpass
logger = logging.getLogger(__name__)

class IntegracaoStandinConta(RemoteBasePlugin):

    def query(self, **kwargs):

        global con, total_lancamentos_standin_conta, state_integracao_standin_conta

        state_integracao_standin_conta = 0.0
        status_ok = "OK"
        status_notok = "Bad"

        try:
            con = cx_Oracle.connect(user="usr_filasmatera", password="dynafilasmatera#2021#", dsn="10.26.27.175/HMATERA")
            cursor = con.cursor()
            print("Successfully connected to Oracle Database")
            consulta_sql = "select 'QCC_LANC_ASSINCRONO' , count(1) from CC_QCC_LANC_ASSINCRONO s where state <> 3"
            cursor.execute(consulta_sql)
            resultado_query = (cursor.fetchall())

            for linha in resultado_query:
                total_lancamentos_standin_conta = (linha[0])
                print("Total Registros", total_lancamentos_standin_conta)

            if total_lancamentos_standin_conta == 0:
                state_integracao_standin_conta = status_ok
                print("Status:", state_integracao_standin_conta)
            else:
                state_integracao_standin_conta = status_notok
                print("Status:", state_integracao_standin_conta)

            group = self.topology_builder.create_group("Filas AQ", "Filas AQ")
            device = group.create_element("Integração Standin > Conta", "Integração Standin > Conta")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="Oracle")
            group.report_property(key="Integrações", value="AWS")
            group.report_property(key="Descrição", value="Filas Oracle AQ - Conta e Standin")
            device.report_property(key="Integrações", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.add_endpoint(ip="10.26.27.175", port=3306, dnsNames=["HMATERA"])
            device.relative(key='total_lancamentos_standin_conta', value=total_lancamentos_standin_conta)
            group.absolute(key='total_lancamentos_standin_conta', value=total_lancamentos_standin_conta)
            device.state_metric(key='state_integracao_standin_conta', value=state_integracao_standin_conta)

        except cx_Oracle.DatabaseError as e:
            print("Erro ao acessar tabela", e)

        finally:
            print("Conexão ao banco encerrada")