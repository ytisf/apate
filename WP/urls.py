"""WP URL Configuration

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
from django.conf.urls import url
from django.contrib import admin

from apate.views import Dashboard, AddNewServer, ViewHosts, RefreshLogs
from apate.views import RemoveMachine, AddNewHoneypot, ViewHoneypots
from apate.views import RemoveHoneypot, StartHoneypot, StopHoneypot
from apate.views import ViewLogEvents, ClearLogs, ClearNotifications
from apate.views import ViewEvents, ClearEvals, DownloadConfigurations
from apate.views import __init

# API Functions
from apate.views import _apiGetLogs, _apiGetEvals, _apiGetHoneypots
from apate.views import _apiGetDevices

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^$', Dashboard),

    url(r'^AddNewServer', AddNewServer),
    url(r'^ViewHosts', ViewHosts),
    url(r'^RemoveMachine', RemoveMachine),
    url(r'^AddNewHoneypot', AddNewHoneypot),
    url(r'^ViewHoneyPots', ViewHoneypots),
    url(r'^RemoveHoneypot', RemoveHoneypot),
    url(r'^StartHoneypot', StartHoneypot),
    url(r'^StopHoneypot', StopHoneypot),
    url(r'^RefreshLogs', RefreshLogs),
    url(r'^ViewLogEvents', ViewLogEvents),
    url(r'^ClearLogs', ClearLogs),
    url(r'^ClearNotifications', ClearNotifications),
    url(r'^ViewEvents', ViewEvents),
    url(r'^ClearEvals', ClearEvals),
    url(r'^DownloadConfigurations', DownloadConfigurations),
    url(r'^api/logs', _apiGetLogs),
    url(r'^api/evals', _apiGetEvals),
    url(r'^api/honeypots', _apiGetHoneypots),
    url(r'^api/devices', _apiGetDevices),
]

__init()
