from django.apps import AppConfig


class CustomersConfig(AppConfig):
    name = 'customers'
    verbose_name = 'Клиенты'

    def ready(self):
        import customers.signals
