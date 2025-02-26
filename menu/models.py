from django.db import models
from localized_fields.fields import LocalizedCharField, LocalizedTextField
from localized_fields.models import LocalizedModel


class AbstractMenuModel(LocalizedModel):
    name = LocalizedCharField(required=True, verbose_name="Наименование")
    is_hidden = models.BooleanField(default=False, verbose_name="Скрыть")
    priority = models.PositiveIntegerField(
        db_index=True,
        default=0,
        verbose_name="Приоритет"
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name.translate()


class Category(AbstractMenuModel):

    class Meta:
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'
        ordering = ('-priority', '-id')


class MenuItem(AbstractMenuModel):
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name='menu_items',
        verbose_name="Категория"
    )
    description = LocalizedTextField(required=True, verbose_name="Описание")
    image = models.ImageField(verbose_name="Картинка")
    price = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Цена")
    is_popular = models.BooleanField(default=False, verbose_name="Популярная позиция")

    class Meta:
        verbose_name = 'Позиция'
        verbose_name_plural = 'Позиции'
        ordering = ('-priority', '-id')
