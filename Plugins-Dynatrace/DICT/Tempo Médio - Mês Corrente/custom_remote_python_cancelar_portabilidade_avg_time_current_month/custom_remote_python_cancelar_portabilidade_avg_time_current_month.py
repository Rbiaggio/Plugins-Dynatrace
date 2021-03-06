import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


# Definindo Classe
class CancelarPortabilidadeCurrentMonth(RemoteBasePlugin):

    def query(self, **kwargs):

        global avg_cancelar_portabilidade_mes_corrente, state_cancelar_portabilidade_mes_corrente,con

        state_cancelar_portabilidade_mes_corrente = 0.0
        status_ok = "OK"
        status_notok = "Bad"

        try:
            con = mysql.connector.connect(host='mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='addressing', user='9001088', password='9001088#2022#')

            consulta_sql = "SELECT a.avg,b.avg FROM (SELECT AVG(TIMESTAMPDIFF(MINUTE, claim.RESOLUTION_PERIOD_END, claim.LAST_MODIFIED)) AVG FROM AD_CLAIM claim WHERE TYPE = 'PORTABILITY'\
                            AND STAKEHOLDER = 'DONOR' AND STATUS = 'CANCELLED' AND OPERATION_REASON = 'DEFAULT_OPERATION' AND claim.RESOLUTION_PERIOD_END > TIMESTAMPADD(DAY, -30, NOW())) a,\
                            (SELECT AVG(TIMESTAMPDIFF(MINUTE, claim.RESOLUTION_PERIOD_END, claim.LAST_MODIFIED)) 'AVG' FROM AD_CLAIM claim WHERE TYPE = 'PORTABILITY'\
                            AND STAKEHOLDER = 'DONOR' AND STATUS = 'CANCELLED' AND OPERATION_REASON = 'DEFAULT_OPERATION' AND claim.RESOLUTION_PERIOD_END >= STR_TO_DATE(CONCAT(DATE_FORMAT(NOW(), '%Y-%m'), '-01'), '%Y-%m-%d')) b"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            resultado_query = (cursor.fetchall())

            for linha in resultado_query:
                avg_cancelar_portabilidade_mes_corrente = (linha[1])
                print("Total Registros", avg_cancelar_portabilidade_mes_corrente)

            if state_cancelar_portabilidade_mes_corrente <= 60.0:
                state_cancelar_portabilidade_mes_corrente = status_ok
                print("Status:", state_cancelar_portabilidade_mes_corrente)
            else:
                state_cancelar_portabilidade_mes_corrente = status_notok
                print("Status:", state_cancelar_portabilidade_mes_corrente)

            group = self.topology_builder.create_group("ANS DICT - SLA M??s Corrente", "ANS DICT - SLA M??s Corrente")
            device = group.create_element("Cancelar Portabilidade - SLA M??s Corrente", "Cancelar Portabilidade - SLA M??s Corrente")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="MySQL")
            group.report_property(key="Integra????es", value="AWS")
            group.report_property(key="Descri????o", value="Diret??rio de Identificadores de Contas Transacionais")
            device.report_property(key="Database Name", value="addressing")
            device.report_property(key="Integra????es", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.report_property(key="Secondary technology", value="MySQL")
            device.add_endpoint(ip="10.28.50.53", port=3306, dnsNames=["mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com"])
            device.relative(key='avg_cancelar_portabilidade_mes_corrente', value=avg_cancelar_portabilidade_mes_corrente)
            group.absolute(key='avg_cancelar_portabilidade_mes_corrente', value=avg_cancelar_portabilidade_mes_corrente)
            device.state_metric(key='state_cancelar_portabilidade_mes_corrente', value=state_cancelar_portabilidade_mes_corrente)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
            if con.is_connected():
                con.close()
                cur.close()
                print("Conex??o ao banco encerrada")