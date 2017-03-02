from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

#
# "included" by mysite/urls.py
# "mvvscrape/" part of url is already stripped off at this point
urlpatterns = patterns('',
    (r'^$', 'emvee.mvvscrape.views.list_issues'),  # default view
    (r'^list_issues$', 'emvee.mvvscrape.views.list_issues'),  
    (r'^list_crimes/(\d+)/$','emvee.mvvscrape.views.list_crimes'),
#    (r'^find_police_logs/go','emvee.mvvscrape.views.go_find_police_logs'),
#    (r'^download_police_logs','emvee.mvvscrape.views.download_police_logs'),
                       
)






