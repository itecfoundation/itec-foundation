from django.urls import include, path, re_path

from wagtail.admin import urls as wagtailadmin_urls
from wagtail.documents import urls as wagtaildocs_urls
from wagtail.core import urls as wagtail_urls


urlpatterns = [
    path('anymail/', include('anymail.urls')),
    re_path(
        r'^photologue/', include('photologue.urls', namespace='photologue')
    ),
    re_path(r'^cms/', include(wagtailadmin_urls)),
    re_path(r'^documents/', include(wagtaildocs_urls)),
    re_path(r'', include(wagtail_urls)),
]