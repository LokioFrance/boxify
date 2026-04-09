import os

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from api.models import HoneypotAttempt
from assets.models import AssetObject, Item, ItemInfo

from .serializers import (
    AssetObjectSerializer,
    HoneypotAttemptSerializer,
    ItemInfoSerializer,
    ItemSerializer,
)


class ItemViewSet(ModelViewSet):
    """CRUD complet pour les boîtes (Items)."""

    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class AssetObjectViewSet(ModelViewSet):
    """CRUD complet pour les objets dans une boîte."""

    queryset = AssetObject.objects.select_related("item").all()
    serializer_class = AssetObjectSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        item_id = self.request.query_params.get("item")
        if item_id:
            qs = qs.filter(item_id=item_id)
        return qs


class ItemInfoViewSet(ModelViewSet):
    """CRUD complet pour les métadonnées d'une boîte (fragile, en mouvement)."""

    queryset = ItemInfo.objects.select_related("item").all()
    serializer_class = ItemInfoSerializer


class HoneypotView(APIView):
    """
    GET /api/honeypot/

    Retourne toutes les tentatives enregistrées par le honeypot.
    Protégé par l'en-tête X-Honeypot-Key (valeur = HONEYPOT_API_KEY).
    """

    permission_classes = [AllowAny]

    def get(self, request):
        expected_key = os.environ.get("HONEYPOT_API_KEY", "")
        if not expected_key:
            return Response(
                {"detail": "HONEYPOT_API_KEY non configurée sur ce service."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        provided_key = request.headers.get("X-Honeypot-Key", "")
        if provided_key != expected_key:
            return Response(
                {"detail": "Non autorisé."}, status=status.HTTP_403_FORBIDDEN
            )

        attempts = HoneypotAttempt.objects.all()
        serializer = HoneypotAttemptSerializer(attempts, many=True)
        return Response(serializer.data)
