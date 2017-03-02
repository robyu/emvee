"""Find police log"""

import sys
import urllib
import re
import time
import logging
import os
from models import PoliceLog

#
# logger for debug 
my_logger=logging.getLogger('mvvscrape/findpolicelog')

#
# location of downloaded files
DOWNLOAD_DIR='./mvvscrape/policelogs'



class NoLogUrl(Exception):
    """
    No URL corresponding to police log"""
    pass

class IOError(Exception):
    """
    IOError occurred while trying to download and write police log"""
    pass

def find_police_log_url(issue_num):
    """
    Given issue number of the MV Voice,
    go find the url of the corresponding police log

    Returns dictionary y with keys:
    issue_exists: boolean
    date:  issue date; standard time-tuple
    url:  string containing URL of police log article; blank if no police log
    """

    #
    # "y" is the output dictionary
    y={'issue_exists':False,'url':'','date':''}

    #
    # compile regexp for "Police Log"
    if issue_num <=0:
        #
        # there is no issue 0, and the mv voice website chokes if given this parameter
        # (it returns the latest issue?)
        return y
    elif issue_num==40:
        #
        # in issue 40, police log renamed to "crime watch"
        police_log_regexp=re.compile(r"<a\shref=(?P<police_log_url>(.*))>"  # match <a href=(URL)>
                                     "Crime\swatch</a>",
                                     re.VERBOSE|re.IGNORECASE)
    else:
        police_log_regexp=re.compile(r"<a\shref=(?P<police_log_url>(.*))>"  # match <a href=(URL)>
                                     "Police\sLog</a>",
                                     re.VERBOSE|re.IGNORECASE)

    
    date_regexp=re.compile(r"(Thursday|Friday)," 
                           "\s?"  # match 0-1 whitespace
                           "(?P<issue_date>"  # group specifier
                           "\w+"   # match 1> alphanum , e.g. February
                           "\s"
                           "\d+"   # match 1> digit, e.g. 3
                           ",\s"
                           "200\d"  # match e.g. 2006
                           ")"   # close parens for group specifier
                           ,re.VERBOSE)
    
    

    url = "http://www.mv-voice.com/toc.php?i=%d" % issue_num
    my_logger.debug('opening url=(%s)',url)


    f=urllib.urlopen(url)

    line_count=0
    for line in f:
        line_count=line_count+1

        match=police_log_regexp.search(line)
        if match:
            y['url']=match.group('police_log_url')
            my_logger.debug('Found url: (%s)', y['url'])
            y['issue_exists']=y['issue_exists'] or True

        match=date_regexp.search(line)
        if match:
            date_string=match.group('issue_date')
            my_logger.debug('Found date: (%s)' , date_string)
            y['issue_exists']=y['issue_exists'] or True

            #
            # convert date to time-tuple format
            y['date']=time.strptime(date_string,'%B %d, %Y')


        
    my_logger.debug('processed (%d) lines',line_count)
    f.close()

    my_logger.debug(y)
    return y


def download_police_logs(start_issue,stop_issue):
    for index in range(start_issue,stop_issue+1):
        try:
            download_police_log(index)
        except PoliceLog.DoesNotExist:
            pass
        except NoLogUrl:
            pass

        
def download_police_log(issue_num,dest_dir=DOWNLOAD_DIR):
    """
    Given issue_number, read URL from DB,
    download the URL and write its contents to a file with
    filename corresponding to issue_number

    returns name of downloaded file
    
    if URL not in DB: exception PoliceLog.DoesNotExist
    if download failed: exception"""

    #
    # get db entry for issue_num
    try:
        police_log = PoliceLog.objects.get(issue_number__exact=issue_num)

    except PoliceLog.DoesNotExist:
        my_logger.debug('cannot download.  issue (%d) not in database' % issue_num)
        raise PoliceLog.DoesNotExist

    log_url = police_log.police_log_url
    if len(log_url)==0:
        my_logger.debug('no url for issue (%d)' % issue_num)
        raise NoLogUrl

    #
    # try to open the URL
    my_logger.debug('opening url=(%s)',log_url)

    try:
        f=urllib.urlopen(log_url)
    except IOError:
        my_logger.debug('failed to open=(%s)',log_url)
        raise IOError

    #
    # create download file
    download_filename=create_download_filename(issue_num)
    full_filename=os.sep.join([dest_dir,download_filename])
    outfile=open(full_filename,mode='w')
    my_logger.debug('create download file %s',full_filename)

    #
    # write contents of url to file
    for line in f:
        outfile.write(line)
        
    f.close()
    outfile.close()
    my_logger.debug('download successful')

    #
    # update db
    police_log.filename=download_filename
    police_log.save()
    
    return download_filename

def create_download_filename(issue_num):
    #
    # create download file
    download_filename='%06u.html' % issue_num

    return download_filename

def sync_download_issue_with_db(issue_num,dir=DOWNLOAD_DIR):
    """
    if there's a police log for issue_num, then
    update the db entry with the filename
    """
    download_filename=create_download_filename(issue_num)

#     try:
#         police_log=PoliceLog.objects.get(issue_number__exact=issue_num)
#     except PoliceLog.DoesNotExist:
#         #
#         # if no existing db entry, then
#         # return
#         return
    police_log=PoliceLog.objects.get(issue_number__exact=issue_num)


    file_exists=os.path.exists(os.sep.join([dir,download_filename]))
    my_logger.debug('download filename: %s' % download_filename)
    my_logger.debug('exists: %d' % file_exists)

    if file_exists:
        police_log.filename=download_filename
        police_log.save()
    else:
        police_log.filename=''
        police_log.save()


        
def scrape_and_populate_db(issue_num_start,issue_num_stop):
    """
    scrape mvv website, identify existing issues in specified range,
    find URL of corresponding police log,
    stuff everything into the db

    illegal issue number (<=0) yields exception PoliceLog.DoesNotExist
    """

    if (issue_num_start<1) or (issue_num_stop<1):
        #
        # no issue numbers less than 1
        raise PoliceLog.DoesNotExist

    for index in range(issue_num_start,issue_num_stop+1):
        y=find_police_log_url(index)

        if (y['issue_exists']==False):
            my_logger.debug('issue (%d) not found' % index)
            pub_date=None
        else:
            #
            # convert pub date to db format
            my_logger.debug('issue (%d) exists' % index)
            pub_time_tuple=y['date']
            pub_date=time.strftime('%Y-%m-%d',pub_time_tuple)


        #
        # stuff into db
        try:
            #
            # try to retrieve pre-existing issue entry from db
            my_police_log=PoliceLog.objects.get(issue_number__exact=index)
        except PoliceLog.DoesNotExist:
            #
            # no existing entry for this issue, 
            # so create new db object and save
            my_logger.debug('============ add new db entry:')
            my_logger.debug('issue number: %d',index)
            my_logger.debug('issue exists: %d',int(y['issue_exists']))
            my_logger.debug('date: %s',y['date'])
            my_logger.debug('url: %s',y['url'])
            
            my_police_log = PoliceLog(issue_number=index,
                                      issue_exists=y['issue_exists'],
                                      pub_date=pub_date,
                                      police_log_url=y['url'])
        else:
            #
            # existing entry, so update
            my_logger.debug('update existing entry')
            
            my_police_log.issue_exists=y['issue_exists']
            my_police_log.pub_date=pub_date
            my_police_log.police_log_ur=y['url']
            
            
        # save updated or new entry
        my_police_log.save()
            

if __name__=="__main__":
    for index in range(38,48):
        y=find_police_log_url(index)
        print "%d %s %s\n" % (index,y['date'],y['url'])
        if y['url']:
            download_police_log(index,y['url'])
        else:
            print "no file to download"
