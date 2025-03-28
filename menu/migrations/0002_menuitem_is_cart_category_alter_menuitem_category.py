# Generated by Django 4.0 on 2025-03-01 23:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('menu', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='menuitem',
            name='is_cart_category',
            field=models.BooleanField(default=False, verbose_name='Товар у кассы'),
        ),
        migrations.AlterField(
            model_name='menuitem',
            name='category',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='menu_items', to='menu.category', verbose_name='Категория'),
        ),
    ]
