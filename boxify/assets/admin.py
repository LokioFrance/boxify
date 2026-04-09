from django.contrib import admin
from .models import Item, AssetObject, ItemInfo

admin.site.register(Item)
admin.site.register(AssetObject)
admin.site.register(ItemInfo)
