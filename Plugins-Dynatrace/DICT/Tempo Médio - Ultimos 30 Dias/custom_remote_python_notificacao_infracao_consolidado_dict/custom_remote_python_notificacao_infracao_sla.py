import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


# Definindo Classe
class NotificacaoInfracaoSLA(RemoteBasePlugin):

    def query(self, **kwargs):

        global sla_consolidado_notificacao_infracao, resultado_sla_consolidado_notificacao_infracao, con

        resultado_sla_consolidado_notificacao_infracao = 0.0
        statusOK = "OK"
        statusNOTOK = "Bad"

        try:
            con = mysql.connector.connect(host='ct-rds-prd-account-dispute.cluster-ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='dispute', user='monitoracao', password='Monit#24x7#Dyna#2022')

            consulta_sql = "SELECT COUNT(*) QTD,\
                           MIN(TIMESTAMPDIFF(HOUR, ir.DICT_CREATION_DATE, ir.DICT_LAST_MODIFIED)) AS MIN_HORAS,\
                                   AVG(TIMESTAMPDIFF(HOUR, ir.DICT_CREATION_DATE, ir.DICT_LAST_MODIFIED)) AS AVG_HORAS,\
                                   MAX(TIMESTAMPDIFF(HOUR, ir.DICT_CREATION_DATE, ir.DICT_LAST_MODIFIED)) AS MAX_HORAS,\
                                   MIN(TIMESTAMPDIFF(DAY, ir.DICT_CREATION_DATE, ir.DICT_LAST_MODIFIED)) AS MIN_DIAS,\
                                   AVG(TIMESTAMPDIFF(DAY, ir.DICT_CREATION_DATE, ir.DICT_LAST_MODIFIED)) AS AVG_DIAS,\
                                   MAX(TIMESTAMPDIFF(DAY, ir.DICT_CREATION_DATE, ir.DICT_LAST_MODIFIED)) AS MAX_DIAS\
                            FROM   DIS_INFRACTION_REPORT ir\
                            WHERE  ir.ID_STATUS = 7\
                              AND  ir.STAKEHOLDER = 'RECEIVER'\
                              AND  ir.CREATION_DATE > TIMESTAMPADD(DAY, -30, NOW());"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            sla_registros = (cursor.fetchall())

            for linha in sla_registros:
                sla_consolidado_notificacao_infracao = (linha[5])
                print("Total Registros", sla_consolidado_notificacao_infracao)

            if sla_consolidado_notificacao_infracao <= 21.0:
                resultado_sla_consolidado_notificacao_infracao = statusOK
                print("Status:", resultado_sla_consolidado_notificacao_infracao)
            else:
                resultado_sla_consolidado_notificacao_infracao = statusNOTOK
                print("Status:", resultado_sla_consolidado_notificacao_infracao)

            group = self.topology_builder.create_group("ANS DICT - SLA", "ANS DICT - SLA")
            device = group.create_element("Notificação Infração - SLA", "Notificação Infração - SLA")
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
            device.relative(key='sla_consolidado_notificacao_infracao',
                            value=sla_consolidado_notificacao_infracao)
            group.absolute(key='sla_consolidado_notificacao_infracao', value=sla_consolidado_notificacao_infracao)
            device.state_metric(key='resultado_sla_consolidado_notificacao_infracao',
                                value=resultado_sla_consolidado_notificacao_infracao)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
            if con.is_connected():
                con.close()
                cur.close()
                print("Conexão ao banco encerrada")
