from django.db import models

class PoliceLog(models.Model):
    # issue number of mv-voice
    # make issue_number primary key to avoid duplicate entries
    issue_number=models.IntegerField(primary_key=True)  

    # does the issue exist?
    issue_exists=models.BooleanField()  

    # publication date; allow null if issue doesn't exist
    pub_date=models.DateField(null=True)   

    # url of police log 
    police_log_url=models.URLField(verify_exists=False,     # don't go check that URL exists
                                   max_length=256,blank=True)  # allow blank entries

    # filename of downloaded police log
    filename=models.CharField(max_length=256,blank=True)
    #
    # some useful reference examples:
    # p = PoliceLog.objects.all().order_by('-issue_number')
    # p.count()

class CrimeReport(models.Model):
    #
    # unique hash string
    # set as primary_key to avoid duplicate entries
    hash=models.CharField(max_length=128,primary_key=True)

    #
    # link crime to police log article
    policelog=models.ForeignKey('PoliceLog')

    #
    # crime category
    category=models.CharField(max_length=255)

    # original text from police log
    # and line number
    original_text=models.CharField(max_length=255)
    line_num=models.IntegerField(max_length=255)

    #
    # address
    address=models.CharField(max_length=255)

    #
    # map scale
    map_scale=models.CharField(max_length=255)

    #
    # map coord
    lat=models.CharField(max_length=255,blank=True)
    long=models.CharField(max_length=255,blank=True)

    #
    # crime date
    date=models.DateField(null=True)
    
