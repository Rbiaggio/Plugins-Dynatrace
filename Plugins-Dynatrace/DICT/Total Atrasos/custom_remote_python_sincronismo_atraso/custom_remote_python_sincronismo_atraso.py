import mysql.connector
from mysql.connector import Error
from ruxit.api.base_plugin import RemoteBasePlugin
import logging

logger = logging.getLogger(__name__)


class SincronismoAtraso(RemoteBasePlugin):

    def query(self, **kwargs):

        global con, resultado_sincronismo

        resultado_sincronismo = "OK"
        statusOK = "OK"
        statusNOTOK = "Bad"

        try:
            con = mysql.connector.connect(host='mip-prd-cluster-addressing-2.ceip7fi02lcw.sa-east-1.rds.amazonaws.com',
                                          database='', user='', password=)
            consulta_sql = "SELECT KEY_TYPE,\
                                   MAX(COALESCE(lastSync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(lastSync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, lastSync.FIRST_CHECK_TIMESTAMP_UTC))) LAST_EXECUTION,\
                                   TIMESTAMPDIFF(HOUR, MAX(COALESCE(lastSync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC, COALESCE(lastSync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, lastSync.FIRST_CHECK_TIMESTAMP_UTC))), NOW()) HORAS_DESTE_ULTIMA\
                            FROM   AD_SYNCHRONIZATION lastSync\
                            WHERE  lastSync.STATUS = 9\
                            GROUP BY lastSync.KEY_TYPE\
                            HAVING TIMESTAMPDIFF(HOUR, MAX(COALESCE(lastSync.CHECK_AFTER_VSYNC_REBUILD_TIMESTAMP_UTC,COALESCE(lastSync.CHECK_AFTER_CID_FILES_ADJUSTS_TIMESTAMP_UTC, lastSync.FIRST_CHECK_TIMESTAMP_UTC))), NOW()) > 35;"

            cursor = con.cursor()
            cursor.execute(consulta_sql)
            count_linhas = len(cursor.fetchall())

            total_linhas_atraso_sincronismo = count_linhas

            if total_linhas_atraso_sincronismo == 0:
                resultado_sincronismo = statusOK
                print("Status:", resultado_sincronismo)
            else:
                resultado_sincronismo = statusNOTOK
                print("Status:", resultado_sincronismo)

            group = self.topology_builder.create_group("ANS DICT - Atrasos", "ANS DICT - Atrasos")
            device = group.create_element("Sincronismo", "Sincronismo")
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
            device.relative(key='total_linhas_atraso_sincronismo',
                            value=total_linhas_atraso_sincronismo)
            group.absolute(key='total_linhas_atraso_sincronismo',
                           value=total_linhas_atraso_sincronismo)
            device.state_metric(key='resultado_sincronismo', value=resultado_sincronismo)
            print("Sincronismo Atraso: ", total_linhas_atraso_sincronismo)

        except Error as e:
            print("Erro ao acessar tabela", e)

        finally:
            cur = con.cursor()
        if con.is_connected():
            con.close()
            cur.close()
            print("Conexão ao banco encerrada")



group = self.topology_builder.create_group(
                "Monitoração Arquivos", "Monitoração Arquivos")
            device = group.create_element("Arquivos CIP", "Arquivos CIP")
            group.report_property(key="Desenvolvedor",
                                  value="César Augusto Costa")
            group.report_property(key="Monitoramento", value="Arquivos")
            group.report_property(
                key="Descrição", value="Diretório de Monitoramento de arquivos")
            device.report_property(key="Monitoramento", value="Arquivos")
            device.report_property(key="Technology", value="Python")
            device.add_endpoint(ip=ip, port=port)
            device.relative(key='hasfile',
                            value=hasfile)
            group.absolute(key='hasfile',
                           value=hasfile)




























