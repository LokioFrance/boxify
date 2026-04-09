from rest_framework.routers import DefaultRouter
from .views import ItemViewSet, AssetObjectViewSet, ItemInfoViewSet

router = DefaultRouter()
router.register(r'items', ItemViewSet, basename='item')
router.register(r'objects', AssetObjectViewSet, basename='object')
router.register(r'item-infos', ItemInfoViewSet, basename='item-info')

urlpatterns = router.urls
