from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from assets.models import AssetObject, Item, ItemInfo


class ItemTests(APITestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Boîte A", sub_area=1)

    # ── LIST ──────────────────────────────────────────────────────────────────

    def test_list_items(self):
        response = self.client.get(reverse("item-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # ── CREATE ────────────────────────────────────────────────────────────────

    def test_create_item(self):
        payload = {"name": "Boîte B", "sub_area": 2}
        response = self.client.post(reverse("item-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Item.objects.count(), 2)

    def test_create_item_missing_name(self):
        response = self.client.post(reverse("item-list"), {"sub_area": 1}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_item_missing_sub_area(self):
        response = self.client.post(reverse("item-list"), {"name": "Boîte C"}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── RETRIEVE ──────────────────────────────────────────────────────────────

    def test_retrieve_item(self):
        response = self.client.get(reverse("item-detail", args=[self.item.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Boîte A")

    def test_retrieve_item_not_found(self):
        response = self.client.get(reverse("item-detail", args=[9999]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def test_update_item(self):
        payload = {"name": "Boîte A (renommée)", "sub_area": 1}
        response = self.client.put(
            reverse("item-detail", args=[self.item.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.item.refresh_from_db()
        self.assertEqual(self.item.name, "Boîte A (renommée)")

    def test_partial_update_item(self):
        response = self.client.patch(
            reverse("item-detail", args=[self.item.id]),
            {"name": "Boîte A bis"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_item(self):
        response = self.client.delete(reverse("item-detail", args=[self.item.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Item.objects.count(), 0)

    def test_delete_item_cascades_to_objects(self):
        AssetObject.objects.create(name="Objet 1", item=self.item)
        self.client.delete(reverse("item-detail", args=[self.item.id]))
        self.assertEqual(AssetObject.objects.count(), 0)


class AssetObjectTests(APITestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Boîte A", sub_area=1)
        self.obj = AssetObject.objects.create(name="Clavier", item=self.item)

    # ── LIST ──────────────────────────────────────────────────────────────────

    def test_list_objects(self):
        response = self.client.get(reverse("object-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    def test_filter_objects_by_item(self):
        other_item = Item.objects.create(name="Boîte B", sub_area=2)
        AssetObject.objects.create(name="Souris", item=other_item)
        response = self.client.get(reverse("object-list"), {"item": self.item.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # ── CREATE ────────────────────────────────────────────────────────────────

    def test_create_object(self):
        payload = {"name": "Écran", "item": self.item.id}
        response = self.client.post(reverse("object-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_object_invalid_item(self):
        payload = {"name": "Écran", "item": 9999}
        response = self.client.post(reverse("object-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── RETRIEVE ──────────────────────────────────────────────────────────────

    def test_retrieve_object(self):
        response = self.client.get(reverse("object-detail", args=[self.obj.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["name"], "Clavier")

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def test_update_object(self):
        payload = {"name": "Clavier mécanique", "item": self.item.id}
        response = self.client.put(
            reverse("object-detail", args=[self.obj.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_object(self):
        response = self.client.patch(
            reverse("object-detail", args=[self.obj.id]), {"name": "Clavier bis"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_object(self):
        response = self.client.delete(reverse("object-detail", args=[self.obj.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(AssetObject.objects.count(), 0)

    def test_delete_object_does_not_delete_item(self):
        self.client.delete(reverse("object-detail", args=[self.obj.id]))
        self.assertEqual(Item.objects.count(), 1)


class ItemInfoTests(APITestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Boîte A", sub_area=1)
        self.info = ItemInfo.objects.create(item=self.item, fragile=True, moving=False)

    # ── LIST ──────────────────────────────────────────────────────────────────

    def test_list_item_infos(self):
        response = self.client.get(reverse("item-info-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)

    # ── CREATE ────────────────────────────────────────────────────────────────

    def test_create_item_info(self):
        other_item = Item.objects.create(name="Boîte B", sub_area=2)
        payload = {"item": other_item.id, "fragile": False, "moving": True}
        response = self.client.post(reverse("item-info-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_item_info_invalid_item(self):
        payload = {"item": 9999, "fragile": False, "moving": False}
        response = self.client.post(reverse("item-info-list"), payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    # ── RETRIEVE ──────────────────────────────────────────────────────────────

    def test_retrieve_item_info(self):
        response = self.client.get(reverse("item-info-detail", args=[self.info.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["fragile"])

    # ── UPDATE ────────────────────────────────────────────────────────────────

    def test_update_item_info(self):
        payload = {"item": self.item.id, "fragile": False, "moving": True}
        response = self.client.put(
            reverse("item-info-detail", args=[self.info.id]), payload, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_partial_update_item_info(self):
        response = self.client.patch(
            reverse("item-info-detail", args=[self.info.id]), {"moving": True}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ── DELETE ────────────────────────────────────────────────────────────────

    def test_delete_item_info(self):
        response = self.client.delete(reverse("item-info-detail", args=[self.info.id]))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_delete_item_info_does_not_delete_item(self):
        self.client.delete(reverse("item-info-detail", args=[self.info.id]))
        self.assertEqual(Item.objects.count(), 1)
