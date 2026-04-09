from django.db import models


class Item(models.Model):
    name = models.CharField(max_length=255)

    # ID venant d’un autre microservice
    sub_area = models.BigIntegerField(db_index=True)

    def __str__(self):
        return self.name


class AssetObject(models.Model):
    name = models.CharField(max_length=255)

    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name="asset_objects"
    )


class ItemInfo(models.Model):
    # Relation 1–1 stricte avec Item
    item = models.OneToOneField(
        Item,
        on_delete=models.CASCADE,
        related_name="info"
    )

    fragile = models.BooleanField(default=False)
    moving = models.BooleanField(default=False)

    def __str__(self):
        return f"Info for {self.item.name}"
