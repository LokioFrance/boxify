from rest_framework import serializers

from api.models import HoneypotAttempt
from assets.models import AssetObject, Item, ItemInfo


class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = "__all__"


class AssetObjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssetObject
        fields = "__all__"


class ItemInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ItemInfo
        fields = "__all__"


class HoneypotAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = HoneypotAttempt
        fields = ["id", "ip", "user_agent", "path", "method", "username", "timestamp"]
