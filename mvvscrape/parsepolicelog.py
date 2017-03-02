import re
import time
import logging
import os
import crimes
from models import PoliceLog
from models import CrimeReport
import datetime
import mapscale
import hashlib
from mvgeocoder import MvGeocoder



my_logger=logging.getLogger('mvvscrape/parsepolicelog')

DOWNLOAD_DIR='./mvvscrape/policelogs'


ROAD_SYNONYMS=['ave.',
               'avenue',
               'blvd.',
               'boulevard',
               'cl.',
               'ct.',
               'court',
               'dr.',
               'drive',
               'ln.',
               'lane',
               'real',
               'rd.',
               'road',
               'st.',
               'street',
               'way',
               ]

#
# parser regexps
# debugging:  use re.database.com
#

#REPORT_DATE_REGEXP=re.compile(r'(?P<month>[0-9]?[0-9]+)' +
#                              '/' +
REPORT_DATE_REGEXP=re.compile(r'(?P<month>[0-9]?[0-9]+)' +   # match group "month"
                              '/' +
                              '(?P<day>[0-9]?[0-9]+)'+ # match group "day"
                              '[<|\s]+')      # match "<" or space
CATEGORY_REGEXP=re.compile('(?P<crime>' +                           #define group 'crime'
                           '|'.join(map(re.escape,crimes.all_crimes())) +
                           ')',
                        re.IGNORECASE)



# block regexp:
# 200 block Rock Ave.
# 200 block N. Rock St.
BLOCK_REGEXP=re.compile(r'^([0-9]+)' +  # address
                        '(\sblock\s)' +
                        '([\sa-z.]+)' +
                        '$',
                        re.IGNORECASE)
# BLOCK_REGEXP=re.compile(r'^([0-9]+)' +  # address
#                         '(\sblock\s)' +
#                         '([\sa-z.]+)' +
#                         '(' +
#                         '|'.join(map(re.escape,ROAD_SYNONYMS))+
#                         ')' +
#                         '$',
#                         re.IGNORECASE)

# exact address regexp:
# test for non-presence of "block"
# and presence of road/ave/blah blah
# 2500 West Middlefield Rd.
EXACT_REGEXP=re.compile(r'^([0-9]+)' +
                        '\s' +
                        '[^b][^l][^o][^c][^k]'+
                        '([\sa-z.]+)' +
                        '\s' +
                        '('+
                        '|'.join(map(re.escape,ROAD_SYNONYMS)) +
                        ')' +
                        '$',
                        re.IGNORECASE)

# intersection regexp:
# Crittenden Lane/N. Shoreline Blvd.
INTERSECTION_REGEXP=re.compile(r'^([\sa-z.]+)'+ # street name
                               '/' +   
                               '([\sa-z.]+)' + # street name
                               '$',
                               re.IGNORECASE)
# INTERSECTION_REGEXP=re.compile(r'^([\sa-z.]+)'+ # street name
#                                '('+
#                                '|'.join(map(re.escape,ROAD_SYNONYMS)) +
#                                ')'+
#                                '/' +   
#                                '([\sa-z.]+)' + # street name
#                                '(' +
#                                '|'.join(map(re.escape,ROAD_SYNONYMS)) +
#                                ')' +
#                                '$',
#                                re.IGNORECASE)
                               


#
# states for parser
STATE_INIT = 0;
STATE_FIND_CATEGORY=1;
STATE_FIND_REPORT=2;

class PoliceLogParser(object):
    def __init__(self,source_dir=DOWNLOAD_DIR,geocoder='MV'):
        #
        # location of html files 
        self.source_dir=source_dir

        #
        # set up geocoder object
        # only the 'mountain view' geocoder is available right now
        if geocoder=='MV':
            self.geocoder=MvGeocoder()
        else:
            raise ValueError


    def extract_crime_category(self,match):
        """extract crime category (see common.CRIME_DICT) from text 
        matching CATEGORY_REGEXP

        IN
        match: match object from re.search

        RETURNS
        corresponding dict value from common.CRIME_DICT"""
    

        #
        # wouldn't be calling this function if we didn't already know there's a match
        assert(match!=None)

        #
        # extract crime category
        line=match.string
        start_index=match.start('crime')
        stop_index=match.end('crime')
        crime_key=line[start_index:stop_index]
        crime_key=crime_key.lower()

        my_logger.debug('match(%d,%d)=%s' % (start_index,stop_index,crime_key))
        
        return crime_key

    def new_police_report(self):
        """
        return new dictionary object with relevant fields 
        extracted from police report"""

        d = {'category':'',
             'original_text':'',
             'line_num':0,
             'address':'',
             'map_scale':mapscale.UNKNOWN,
             'date_month':0,
             'date_day':0,
             'date_year':0,
             'lat':'',
             'long':''}

        return d

    def parse_report_line(self,line):
        """
        Parse report entry, extract relevant fields.
        Return a dictionary (see new_police_report)
    
        examples:
        BLOCK
        <p class=story_text>200 block Rock St., 1/29<P></p>
        <p class=story_text>1900 block Rock St., 1/29 (recovered)<P></p>
        
        EXACT
        <p class=story_text>2500 West Middlefield Rd., 1/28<P></p>
        
        
        INTERSECTION
        <p class=story_text>Crittenden Lane/N. Shoreline Blvd., 1/30<P></p>
        
        ESTABLISHMENT
        <p class=story_text>McDonald's, El Monte, 1/29<P></p>
        <p class=story_text>Target, 1/26<P></p>
        <p class=story_text>Safeway, North Shoreline Blvd., 1/25 <P></p>
        
        OTHER
        <p class=story_text>Downtown Mountain View, 1/23<P></p>
        """

        report = self.new_police_report()
        report['original_text'] = line
        
        #
        # extract month and day
        match_date = REPORT_DATE_REGEXP.search(line)
        assert(match_date)
        start_index=match_date.start('month')
        stop_index=match_date.end('month')
        report['date_month'] = int(line[start_index:stop_index])

        start_index=match_date.start('day')
        stop_index=match_date.end('day')
        report['date_day'] = int(line[start_index:stop_index])

        my_logger.debug('extracted date (%d/%d)' % (report['date_month'],report['date_day']))

        #############################################
        # extract location & scale
        line = line[0:match_date.start('month')-1]   # truncate after start of date
        
        #
        # trim off preceding html and trailing comma
        start_index=line.rfind('>')+1
        assert(start_index>0)

        stop_index=line.rfind(',',start_index)
    
        if stop_index >= 2:
            #
            # found a comma, 
            line = line[start_index:stop_index]
        else:
            #
            # no comma found
            line = line[start_index:]
        my_logger.debug('truncated string: (%s)' % line)
        report['address']=line
        #
        # try to determine which case:
        # a block
        # an exact address
        # an establishment
        # an intersection
        # special cases, like: "downtown mountain view"
        # 

        if (BLOCK_REGEXP.match(line)!=None):
            my_logger.debug('BLOCK detected')
            report['map_scale']=mapscale.BLOCK
        elif (INTERSECTION_REGEXP.match(line)!=None):
            my_logger.debug('INTERSECTION detected')
            report['map_scale']=mapscale.INTERSECTION
        elif (EXACT_REGEXP.match(line)!=None):
            my_logger.debug('EXACT detected')
            report['map_scale']=mapscale.EXACT
        else:
            #
            # must be manually assigned
            report['map_scale']=mapscale.OTHER


        return report
    

    def parse_log(self,filename,log_year):
        """
        Given filename of HTML police log, parse it and return list of police reports
        
        In:
        filename - filename of police log
        log_year - year of report

        
        Out:
        List of police report dictionaries (see new_police_report)"""

    
        download_filename=os.sep.join([self.source_dir,filename])
        my_logger.debug("parsing log file: %s" % download_filename)
        try:
            f = open(download_filename,mode='rt')
        except IOError:
            my_logger.debug( "can't open file %s" % download_filename)
            return

        #
        # return list of report objects
        L=[]

        #
        # parse & extract fields into new report object
        # parse to determine exact category
        # parse to determine geoscope
        state = STATE_INIT
        new_state = STATE_INIT
        current_crime_category=None
        line_index = 0
        previous_report_index=0
        for line in f:
            line_index=line_index+1
            #
            # state machine:
            # transition from init -> find_category 
            # transition from find_category to find_report after finding first category

            if state==STATE_INIT:
                new_state = STATE_FIND_CATEGORY

            elif state==STATE_FIND_CATEGORY:
                #
                # find first instance of crime category heading
                match_crime_header = CATEGORY_REGEXP.search(line)
                match_report=REPORT_DATE_REGEXP.search(line)
            
                if match_crime_header and (match_report==None):
                    #
                    # found crime header
                    my_logger.debug("========== TRANSITION TO FIND_REPORT\n")
                    my_logger.debug('%d %s' % (line_index,line))
                    new_state = STATE_FIND_REPORT

                    #
                    # remember where this category occurred
                    category_line_index=line_index

                    current_crime_category = self.extract_crime_category(match_crime_header)
            
                elif match_crime_header and match_report:
                    #
                    # error: both detectors triggered by this line
                    my_logger.debug('match_crime_header and match_report triggered by (%s)' % line)
                    raise ValueError
                elif (match_crime_header==None) and (match_report):
                    #
                    # error: found report line before first category
                    my_logger.debug("found report prematurely in (%s)\n" % line)
                    raise ValueError
                else:
                    #
                    # neither crime header nor crime report, so ignore it
                    pass

            elif state==STATE_FIND_REPORT:
                my_logger.debug('%d %s' % (line_index,line[0:-1])) # -1 to avoid extra LF
        
                #
                # sanity check:
                # "run" of valid reports is too long
                if (category_line_index-line_index) > 20:
                    my_logger.debug("run of reports too long: skipped category?")
                    raise ValueError

                match_crime_header = CATEGORY_REGEXP.search(line)
                match_report=REPORT_DATE_REGEXP.search(line)

                if match_crime_header and (match_report==None):
                    #
                    # came across new crime category
                    current_crime_category = self.extract_crime_category(match_crime_header)
                    new_state = STATE_FIND_REPORT

                    category_line_index=line_index

                elif (match_crime_header==None) and match_report:
                    #
                    # found report
                    new_state = STATE_FIND_REPORT

                    report=self.parse_report_line(line)
                    report['category']=current_crime_category
                    report['line_num']=line_index
                    report['date_year']=log_year
                    L.append(report)

                    #
                    # sanity check
                    # reports should be <= 2 lines apart
                    if (line_index - max([category_line_index,previous_report_index])) > 2:
                        my_logger.debug('WARNING: possible skipped report')
                        my_logger.debug('current line: %d' % line_index)
                        my_logger.debug('last report or category: %d' %
                                        max([category_line_index,previous_report_index]))

                    # remember this line index
                    previous_report_index=line_index

                else:
                    #
                    # neither regexp matched, so ignore it
                    pass

            state=new_state

        f.close()
        return L


    def parse_log_and_populate_db(self,start_issue,stop_issue):
        """
        if issue_num doesn't exist, then skip to next"""
        
        for issue_num in range(start_issue,stop_issue+1):
            try:
                police_log=PoliceLog.objects.get(issue_number__exact=issue_num)
            except PoliceLog.DoesNotExist:
                #
                # if issue doesn't exist in db, then go to next issue
                pass
            else:
                if len(police_log.filename)>0:
                    #
                    # in order to parse log file, must have filename
                    L=self.parse_log(police_log.filename,
                                police_log.pub_date.year)

                else:
                    L=[]
    
                #
                # add each report to db
                for report in L:
                    #
                    # hash string is digest of (issue_number, crime category, original text)
                    # this should ensure a unique hash
                    hasher = hashlib.md5()
                    hasher.update(str(police_log.issue_number))
                    hasher.update(report['category'])
                    hasher.update(report['original_text'])

                    crime=CrimeReport(hash=hasher.hexdigest(),
                                      policelog=police_log,  # foreign key: specify police log object
                                      category=report['category'],
                                      original_text=report['original_text'],
                                      line_num=report['line_num'],
                                      address=report['address'],
                                      map_scale=report['map_scale'],
                                      date=datetime.date(report['date_year'],
                                                         report['date_month'],
                                                         report['date_day']))
                

                    # add lat-long coordinates to crime report
                    (lat,long)=self.geocoder.geocode(crime.address,crime.map_scale)
                    crime.lat=lat
                    crime.long=long

                    crime.save()

    

