# noinspection PyPackageRequirements
"""elixir_daisy URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include

from core.forms.user import UserAuthForm
from web.urls import web_urls

urlpatterns = [
    url(r'^login/$', auth_views.LoginView.as_view(), name='login', kwargs={"authentication_form": UserAuthForm}),
    url(r'^logout/$', auth_views.LogoutView.as_view(), name='logout'),
    url(r'^admin/', admin.site.urls),
    url(r'', include(web_urls)),
]

# Custom error views, see e.g. 
# https://docs.djangoproject.com/en/2.2/ref/settings/#std:setting-CSRF_FAILURE_VIEW
from web.views.error_views import custom_400, custom_403, custom_404, custom_500
handler400 = custom_400
handler403 = custom_403
handler404 = custom_404
handler500 = custom_500

if settings.DEBUG:
    import debug_toolbar
    from django.conf.urls.static import static

    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
