import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


# Definindo Classe
class ConfirmarReivindicacaoSLA(RemoteBasePlugin):

    def query(self, **kwargs):

        global sla_consolidado_confirmar_reivindicacao, resultado_sla_consolidado_confirmar_reivindicacao,con

        resultado_sla_consolidado_confirmar_reivindicacao = 0.0
        statusOK = "OK"
        statusNOTOK = "Bad"

        try:
            con = mysql.connector.connect(host='mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='addressing', user='9001088', password='9001088#2022#')

            consulta_sql = "SELECT MIN(TIMESTAMPDIFF(MINUTE, claim.RESOLUTION_PERIOD_END, claim.LAST_MODIFIED)) MIN,\
                                AVG(TIMESTAMPDIFF(MINUTE, claim.RESOLUTION_PERIOD_END, claim.LAST_MODIFIED)) AVG,\
                                MAX(TIMESTAMPDIFF(MINUTE, claim.RESOLUTION_PERIOD_END, claim.LAST_MODIFIED)) MAX\
                                FROM   AD_CLAIM claim\
                                WHERE  TYPE = 'OWNERSHIP'\
                                AND  STAKEHOLDER = 'DONOR'\
                                AND  STATUS = 'CONFIRMED'\
                                AND  OPERATION_REASON = 'DEFAULT_OPERATION'\
                                AND  claim.RESOLUTION_PERIOD_END > TIMESTAMPADD(DAY, -30, NOW());"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            sla_registros = (cursor.fetchall())

            for linha in sla_registros:
                sla_consolidado_confirmar_reivindicacao = (linha[1])
                print("Total Registros", sla_consolidado_confirmar_reivindicacao)

            if sla_consolidado_confirmar_reivindicacao <= 60.0:
                resultado_sla_consolidado_confirmar_reivindicacao = statusOK
                print("Status:", resultado_sla_consolidado_confirmar_reivindicacao)
            else:
                resultado_sla_consolidado_confirmar_reivindicacao = statusNOTOK
                print("Status:", resultado_sla_consolidado_confirmar_reivindicacao)

            group = self.topology_builder.create_group("ANS DICT - SLA", "ANS DICT - SLA")
            device = group.create_element("Confirmar Reivindicação - SLA", "Confirmar Reivindicação - SLA")
            group.report_property(key="Desenvolvedor", value="Rodrigo Biaggio")
            group.report_property(key="Secondary technology", value="MySQL")
            group.report_property(key="Integrações", value="AWS")
            group.report_property(key="Descrição", value="Diretório de Identificadores de Contas Transacionais")
            device.report_property(key="Database Name", value="addressing")
            device.report_property(key="Integrações", value="AWS")
            device.report_property(key="Technology", value="Python")
            device.report_property(key="Secondary technology", value="MySQL")
            device.add_endpoint(ip="10.28.50.53", port=3306,
                                dnsNames=["mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com"])
            device.relative(key='sla_consolidado_confirmar_reivindicacao', value=sla_consolidado_confirmar_reivindicacao)
            group.absolute(key='sla_consolidado_confirmar_reivindicacao', value=sla_consolidado_confirmar_reivindicacao)
            device.state_metric(key='resultado_sla_consolidado_confirmar_reivindicacao',
                                value=resultado_sla_consolidado_confirmar_reivindicacao)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
            if con.is_connected():
                con.close()
                cur.close()
                print("Conexão ao banco encerrada")
