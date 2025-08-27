from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path, include

from core.forms.user import UserAuthForm
from web.urls import web_urls
from notification.urls import notif_urls

urlpatterns = [
    path(
        "login/",
        auth_views.LoginView.as_view(authentication_form=UserAuthForm),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("admin/", admin.site.urls),
    path("notifications/", include(notif_urls)),
    path("", include(web_urls)),
]

from web.views.error_views import custom_400, custom_403, custom_404, custom_500

handler400 = custom_400
handler403 = custom_403
handler404 = custom_404
handler500 = custom_500

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
