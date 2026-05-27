"""뱅크다(Bankda) REST API 클라이언트.

인수인계 2026-05-15 §6 명세 + 통합 2026-05-25.
호출 방향: Django (outbound) → 뱅크다 a.bankda.com.
"""
import logging

import requests
from django.conf import settings

logger = logging.getLogger(__name__)

BANKDA_URL = 'https://a.bankda.com/dtsvc/bank_tr.php'


class BankdaError(Exception):
    pass


class BankdaClient:
    def __init__(self):
        self.access_token = settings.BANKDA_ACCESS_TOKEN
        self.account_num = settings.BANKDA_ACCOUNT_NUM
        self.is_test = settings.BANKDA_IS_TEST

    def fetch_transactions(self, last_bcode=None, datefrom=None, dateto=None):
        if not self.access_token:
            raise BankdaError('BANKDA_ACCESS_TOKEN 미설정')
        if not last_bcode and not (datefrom and dateto):
            raise BankdaError('last_bcode 또는 datefrom/dateto 중 하나 필수')

        # 일부 HTTP 서버가 underscore 헤더 거부 — body에도 박아서 양쪽 전달
        data = {
            'datatype': 'json',
            'charset': 'utf8',
            'istest': self.is_test,
            'access_token': self.access_token,
        }
        if self.account_num:
            data['accountnum'] = self.account_num
        if last_bcode:
            data['bcode'] = str(last_bcode)
        if datefrom and dateto:
            data['datefrom'] = datefrom
            data['dateto'] = dateto

        headers = {
            'access_token': self.access_token,
            'Access-Token': self.access_token,
        }

        try:
            response = requests.post(BANKDA_URL, headers=headers, data=data, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error('bankda HTTP 실패: %s', exc)
            raise BankdaError(f'HTTP 호출 실패: {exc}') from exc

        try:
            payload = response.json()
        except ValueError as exc:
            logger.error('bankda JSON 파싱 실패: %s', response.text[:200])
            raise BankdaError(f'JSON 파싱 실패: {exc}') from exc

        description = (payload.get('response') or {}).get('description') or ''
        if description:
            logger.warning('bankda description: %s', description)

        return payload
