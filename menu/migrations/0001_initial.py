# Generated by Django 4.0 on 2025-02-23 13:37

from django.db import migrations, models
import django.db.models.deletion
import localized_fields.fields.char_field
import localized_fields.fields.text_field
import localized_fields.mixins
import psqlextra.manager.manager


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', localized_fields.fields.char_field.LocalizedCharField(required=['ru', 'uz'], verbose_name='Наименование')),
                ('is_hidden', models.BooleanField(default=False, verbose_name='Скрыть')),
                ('priority', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Приоритет')),
            ],
            options={
                'verbose_name': 'Категория',
                'verbose_name_plural': 'Категории',
                'ordering': ('-priority', '-id'),
            },
            bases=(localized_fields.mixins.AtomicSlugRetryMixin, models.Model),
            managers=[
                ('objects', psqlextra.manager.manager.PostgresManager()),
            ],
        ),
        migrations.CreateModel(
            name='MenuItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', localized_fields.fields.char_field.LocalizedCharField(required=['ru', 'uz'], verbose_name='Наименование')),
                ('is_hidden', models.BooleanField(default=False, verbose_name='Скрыть')),
                ('priority', models.PositiveIntegerField(db_index=True, default=0, verbose_name='Приоритет')),
                ('description', localized_fields.fields.text_field.LocalizedTextField(required=['ru', 'uz'], verbose_name='Описание')),
                ('image', models.ImageField(upload_to='', verbose_name='Картинка')),
                ('price', models.DecimalField(decimal_places=2, max_digits=12, verbose_name='Цена')),
                ('is_popular', models.BooleanField(default=False, verbose_name='Популярная позиция')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='menu_items', to='menu.category', verbose_name='Категория')),
            ],
            options={
                'verbose_name': 'Позиция',
                'verbose_name_plural': 'Позиции',
                'ordering': ('-priority', '-id'),
            },
            bases=(localized_fields.mixins.AtomicSlugRetryMixin, models.Model),
            managers=[
                ('objects', psqlextra.manager.manager.PostgresManager()),
            ],
        ),
    ]
