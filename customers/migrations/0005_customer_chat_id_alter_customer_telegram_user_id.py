# Generated by Django 4.0 on 2025-03-01 15:58

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customers', '0004_deliveryzone'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='chat_id',
            field=models.BigIntegerField(default=1, verbose_name='Chat ID'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='customer',
            name='telegram_user_id',
            field=models.BigIntegerField(unique=True, verbose_name='Telegram user ID'),
        ),
    ]
