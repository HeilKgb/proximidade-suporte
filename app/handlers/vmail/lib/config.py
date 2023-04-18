"""
Copyright(C) Venidera Research & Development, Inc - All Rights Reserved
Unauthorized copying of this file, via any medium is strictly prohibited
Proprietary and confidential
Written by Marcos Leone Filho <marcos@venidera.com>
"""


def get_config(config_name='aws'):
    """ Returns a given configuration set for smtp """
    smtp_configs = {
        "aws": {
            "smtp_server": "email-smtp.us-east-1.amazonaws.com",
            "smtp_username": "AKIAIEYCWNP5GKVC65KA",
            "smtp_password": "AklvPOj5k9vPG2/tXyiTBhNaWCR9Lw5BuCcmgoIvemuA",
            "smtp_port": "587"}}
    return smtp_configs[config_name]
