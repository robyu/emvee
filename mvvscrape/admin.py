from emvee.mvvscrape.models import PoliceLog,CrimeReport
from django.contrib import admin

class PoliceLogAdmin(admin.ModelAdmin):
    list_display=('issue_number','issue_exists','pub_date','police_log_url')
    list_filter = ["issue_number"]

class CrimeReportAdmin(admin.ModelAdmin):
    list_display=('date','category','original_text','line_num','address','map_scale','lat','long')
    list_filter = ['date']

admin.site.register(CrimeReport,CrimeReportAdmin)

admin.site.register(PoliceLog,PoliceLogAdmin)
