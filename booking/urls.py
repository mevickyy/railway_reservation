"""api URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
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
from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'book/$', views.BookTicket.as_view(), name="book_ticket"),
    url(r'cancel/(?P<pk>\d+)/$', views.CancelTicket.as_view(), name="cancel"),
    url(r'printbookedticket/$', views.PrintBookedTicket.as_view(), name="print_booked_ticket"),
    url(r'printavailableticket/$', views.PrintAvailableTicket.as_view(), name="print_available_ticket"),
    url(r'search_by_pnr_ticket/(?P<pk>.*)/$', views.SearchPNRTickets.as_view(), name="search_by_pnr_ticket")
]



