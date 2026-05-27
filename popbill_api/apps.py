from django.apps import AppConfig


class PopbillApiConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'popbill_api'
    verbose_name = '팝빌 연동 (입금확인/현금영수증)'
