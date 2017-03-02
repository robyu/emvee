from django.http import HttpResponse
from django.template import Context, loader
from emvee.mvvscrape.models import PoliceLog,CrimeReport
import findpolicelog
import datetime
import time
import logging
import parsepolicelog
from mvgeocoder import MvGeocoder
#
# ACHTUNG:  make sure the template base directory
# is specified in settings.TEMPLATE_DIRS

my_logger=logging.getLogger('mvvscrape.views')

def list_crimes(request,issue_number):

    #
    # get list of crimes
    crime_list = CrimeReport.objects.filter(policelog__issue_number__exact=issue_number)

    if (request.method != 'POST'):
        #
        # method will be 'GET' if we didn't get here via form submit
        pass
    else:
        k=request.POST.keys()
        my_logger.debug(k)
        if 'geocode' in k:
            my_logger.debug('geocode pushed')
            
            #
            # geocode the entries in the list
            geocoder=MvGeocoder()
            for index in range(0,len(crime_list)):
                crime=crime_list[index]
                (lat,long)=geocoder.geocode(crime.address,crime.map_scale)
                crime_list[index].lat=lat
                crime_list[index].long=long
            

    template=loader.get_template('mvvscrape/list_crimes.html')
    context = Context({'crime_list': crime_list,'issue_number':issue_number})
    return HttpResponse(template.render(context))


def list_issues(request):
    """List all Voice issues in the database
    """

    my_logger.debug('request.method=(%s)' % request.method)
    my_logger.debug('request.POST=(%s)' % request.POST)

    #
    # default status message
    message='Hello!\n'

    if (request.method != 'POST'):
        #
        # method will be 'GET' if we didn't get here via form submit
        pass
    else:
        try:
            start_issue=int(request.POST['start_index'])
            stop_issue=int(request.POST['stop_index'])
        except ValueError:
            #
            # invalid strings passed as start_index and stop_index
            start_issue=0;
            stop_issue=0;
        
        #
        # identify which button was pressed
        k=request.POST.keys()
        my_logger.debug(k)
        if 'find' in k:
            #
            # user wants to find logs
            message = message + ('find (%d..%d)\n' % (start_issue,stop_issue))
            my_logger.debug('find police logs')
            try:
                findpolicelog.scrape_and_populate_db(start_issue,stop_issue)
            except PoliceLog.DoesNotExist:
                message=message + 'Illegal index range (%d,%d)\n' % (start_issue,stop_issue)
        elif 'download' in k:
            #
            # user wants to download police log
            message = message + ('download (%d..%d)\n' % (start_issue,stop_issue))
            my_logger.debug('download police logs')

            findpolicelog.download_police_logs(start_issue,stop_issue)
        elif 'parse' in k:
            #
            # user wants to parse downloaded log
            message = message + ('parse (%d..%d)' % (start_issue,stop_issue))

            parsepolicelog.parse_log_and_populate_db(start_issue,stop_issue)

        else:
            message = message + 'Unidentified button\n'

    #
    # list issues in db
    issue_list = PoliceLog.objects.all().order_by('-issue_number')
    template=loader.get_template('mvvscrape/list_issues.html')


    # determine whether associated crime reports exist
    # iterate through issue_list
    # for each issue, locate if any corresponding crimeporets in database
    # if so, then modify issue object
    for index in range(0,len(issue_list)):
        #
        # any crime rpeorts associated with this issue number?
        issue_number = issue_list[index].issue_number
        crimereport_list = CrimeReport.objects.filter(policelog__issue_number__exact=issue_number)

        #
        # bind a new attribute to the issue called "has_crime_reports"
        if len(crimereport_list):
            issue_list[index].has_crime_reports=str(issue_list[index].issue_number)
        else:
            issue_list[index].has_crime_reports=None
        my_logger.debug('issue[%d]: %d %s' % (index,
                                            issue_list[index].issue_number,
                                            issue_list[index].has_crime_reports))


    #
    # build context dictionary
    context = Context({'issue_list': issue_list,'message':message})

    return HttpResponse(template.render(context))







