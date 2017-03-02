import unittest
import models
import findpolicelog
import parsepolicelog
from models import PoliceLog
from models import CrimeReport
import time
import datetime
import shutil
import crimes
import os
import mapscale
from mvgeocoder import MvGeocoder

TEST_DATA_IN='mvvscrape/test_data'
TEST_DATA_OUT='mvvscrape/test_out'
USE_WEB=False

def get_crime_type_distribution(crime_report_list):
    category_distrib={}
    for crime in crime_report_list:
        #
        # distribution of crime categories
        category=crime.category
        if category_distrib.has_key(category):
            category_distrib[category]=category_distrib[category]+1
        else:
            category_distrib[category]=1
            
    return category_distrib

def get_mapscale_distribution(crime_report_list):
    scale_distrib={}
    for crime in crime_report_list:
        #
        # distribution of map scales
        scale=crime.map_scale
        if scale_distrib.has_key(scale):
            scale_distrib[scale]=scale_distrib[scale]+1
        else:
            scale_distrib[scale]=1
            
    return scale_distrib
        
class TestParser(unittest.TestCase):
    def test_sanity(self):
        self.assertEquals(1,1)

class TestFindPoliceLog(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass



    def test_sanity(self):
        self.assertEquals(1,1)

    def test_find_single_log(self):
        """
        get single issue's policelog info, populate db"""
        if USE_WEB:
            issue_num=39
            findpolicelog.scrape_and_populate_db(issue_num,issue_num)

            try:
                police_log=PoliceLog.objects.get(issue_number__exact=issue_num)

            except PoliceLog.DoesNotExist:
                #
                # couldn't retrieve db entry
                self.assertEquals(0,1)
            else:
                self.assertEquals(police_log.issue_exists,True)
                self.assertEquals(police_log.pub_date,datetime.date(2006,2,10))
                url='http://www.mv-voice.com/story.php?story_id=985'
                self.assertEquals(police_log.police_log_url,url)

    def test_find_same_issue_twice(self):
        """
        try scraping same issue twice, check results in db"""

        if USE_WEB:
            issue_num=39
            
            #
            # scrape same issue twice
            findpolicelog.scrape_and_populate_db(issue_num,issue_num)
            findpolicelog.scrape_and_populate_db(issue_num,issue_num)
            
            #
            # should only be one entry in the db
            self.assertEquals(1,len(PoliceLog.objects.all()))

    def test_find_two_issues(self):
        """
        find police log in 2 issues"""

        if USE_WEB:
            issue_num=39
            
            #
            # scrape same issue twice
            findpolicelog.scrape_and_populate_db(issue_num,issue_num+1)
            
            
            #
            # should be 2 entries in the db
            issue_list=PoliceLog.objects.all()
            self.assertEquals(2,len(issue_list))



    def test_handle_no_policelog(self):
        """
        handle non-existing police log
        issue 44
        2006-03-17"""
        
        if USE_WEB:
            issue_num=44
            findpolicelog.scrape_and_populate_db(issue_num,issue_num)

            try:
                police_log=PoliceLog.objects.get(issue_number__exact=issue_num)


            except PoliceLog.DoesNotExist:
                #
                # couldn't retrieve db entry
                self.assertEquals(0,1)
            else:
                #
                # issue exists, but no police log
                self.assertEquals(police_log.issue_exists,True)
                #
                # police log url is blank
                self.assert_(len(police_log.police_log_url)==0)
                
                self.assertEquals(police_log.pub_date,datetime.date(2006,3,17))


    def test_nonexistent_issue0(self):
        """
        user asks for issue 0"""

        ##################3
        # mvv website chokes on issue 0
        issue_num=0

        #


        #
        # expect zero entries 
        try:
            findpolicelog.scrape_and_populate_db(issue_num,issue_num)
            police_log=PoliceLog.objects.get(issue_number__exact=issue_num)

        #
        # expect exception
        except PoliceLog.DoesNotExist:
            pass
        else:
            self.assert_(1)

    def test_nonexistent_issue1(self):
        """
        user asks for issue 1"""
        if USE_WEB:
            ######################3
            # issue 1 doesn't exist either
            issue_num=1

            #
            findpolicelog.scrape_and_populate_db(issue_num,issue_num)

            #
            # expect 1 entry with no pub date
            try:
                police_log=PoliceLog.objects.get(issue_number__exact=issue_num)

            #
            # expect exception
            except PoliceLog.DoesNotExist:
                self.assert_(0)

            self.assertEquals(police_log.issue_exists,False)
            self.assertEquals(police_log.pub_date,None)

    def test_download(self):
        """
        try to download existing url"""
        if USE_WEB:
            issue_num=39

            #
            findpolicelog.scrape_and_populate_db(issue_num,issue_num)


            #
            # expect 1 entry 
            try:
                police_log=PoliceLog.objects.get(issue_number__exact=issue_num)

            #
            # expect exception
            except PoliceLog.DoesNotExist:
                self.assert_(0)

            #
            # download url
            fname=findpolicelog.download_police_log(issue_num,TEST_DATA_OUT)

            #
            # file was downloaded?
            target_filename=findpolicelog.create_download_filename(issue_num)
            self.assert_(os.path.exists(
                    os.sep.join([TEST_DATA_OUT,target_filename])))

            #
            # delete file
            try:
                os.remove(target_filename)
            except:
                pass


    def test_sync_file0(self):
        """
        try to update db filename entry w/ file in directory"""


        #
        # set up database
        issue_num=38
        police_log=PoliceLog(issue_number=issue_num,
                             issue_exists=True)
        police_log.save()

        #
        # try to update
        test_dir=TEST_DATA_IN
        findpolicelog.sync_download_issue_with_db(issue_num,test_dir)

        try:
            police_log=PoliceLog.objects.get(issue_number__exact=issue_num)
        except PoliceLog.DoesNotExist:
            self.assert_(0)

        #
        # at this point, filename should be filled in
        self.assert_(len(police_log.filename)>0)

    def test_sync_file1(self):
        """
        try to update db filename entry w/ non-existing log file"""

        #
        # set up database
        issue_num=999
        police_log=PoliceLog(issue_number=issue_num,
                             issue_exists=True)
        police_log.save()

        #
        # try to update
        test_dir=TEST_DATA_IN
        findpolicelog.sync_download_issue_with_db(issue_num,test_dir)

        police_log=PoliceLog.objects.get(issue_number__exact=issue_num)

        #
        # at this point, filename should be blank
        self.assert_(len(police_log.filename)==0)



class TestParsePoliceLog(unittest.TestCase):
    database_populated=False

    def setUp(self):
        print 'setUp: database_populated=%s' % self.database_populated
        if TestParsePoliceLog.database_populated==False:
            #
            # set up database
            issue_num=39
            police_log=PoliceLog(issue_number=issue_num,
                                 issue_exists=True,
                                 pub_date=datetime.date(2006,3,10))
            police_log.save()

            #
            # associate db entry with 
            # log file in test directory 
            test_dir=TEST_DATA_IN
            findpolicelog.sync_download_issue_with_db(issue_num,test_dir)

            # 
            # parse crime log and load crimes into db
            p=parsepolicelog.PoliceLogParser(test_dir)
            p.parse_log_and_populate_db(issue_num,issue_num)

            #
            # remember that we've performed setup
            TestParsePoliceLog.database_populated=True
        else:
            pass

    def test_sanity(self):
        self.assertEquals(1,1)

    def test_map_scale_id(self):
        p = parsepolicelog.PoliceLogParser()

        line="<p class=story_text>200 block Rock St., 1/29<P></p>"
        report=p.parse_report_line(line)
        self.assert_(report['map_scale']==mapscale.BLOCK)
        self.assert_(report['date_month']==1)             
        self.assert_(report['date_day']==29)        

        line="<p class=story_text>2500 West Middlefield Rd., 12/30<P></p>"
        report=p.parse_report_line(line)
        self.assert_(report['map_scale']==mapscale.EXACT)
        self.assert_(report['date_month']==12)             
        self.assert_(report['date_day']==30)        

        line="<p class=story_text>Crittenden Lane/N. Shoreline Blvd., 1/30<P></p>"
        report=p.parse_report_line(line)
        self.assert_(report['map_scale']==mapscale.INTERSECTION)
        self.assert_(report['date_month']==1)             
        self.assert_(report['date_day']==30)        

        line="<p class=story_text>Safeway, North Shoreline Blvd., 1/25 <P></p>"
        report=p.parse_report_line(line)
        self.assert_(report['map_scale']==mapscale.OTHER)
        self.assert_(report['date_month']==1)             
        self.assert_(report['date_day']==25)        

    def test_parse_short_log(self):
        """
        parse short_log.html"""

        p=parsepolicelog.PoliceLogParser(source_dir=TEST_DATA_IN)
        L=p.parse_log("short_log.html",2009)


        #
        # two reports in short_log.html
        self.assert_(len(L)==2)

        #
        # verify first report
	#</table>Auto Burglary <P></p>
        #<p class=story_text>2100 block Creeden Way, 1/23<P></p>
        R=L[0]
        self.assert_(R['category']=='auto burglary')
        self.assert_(R['date_day']==23)
        self.assert_(R['date_month']==1)
        self.assert_(R['date_year']==2009)
        self.assert_(R['address'].lower()=='2100 block creeden way')
        self.assert_(R['map_scale']==mapscale.BLOCK)

        # verify report
        #<p class=story_text>Commercial Burglary<P></p>
        #<p class=story_text>California St./S. Rengstorff Ave., 2/26<P></p>
        R=L[1]
        self.assert_(R['category']=='commercial burglary')
        self.assert_(R['date_day']==26)
        self.assert_(R['date_month']==2)
        self.assert_(R['date_year']==2009)
        self.assert_(R['address'].lower()=='california st./s. rengstorff ave.')
        self.assert_(R['map_scale']==mapscale.INTERSECTION)
        
    def test_parse_000038(self):
        """
        parse 000038.html"""

        p=parsepolicelog.PoliceLogParser(TEST_DATA_IN)
        L=p.parse_log("000038.html",2009)
        
        #
        # should be 70 crime reports in 000038
        self.assert_(len(L)==70)


        #
        # check distribution of parsed crimes
        distrib={}
        for crime in L:
            category=crime['category']
            if distrib.has_key(category):
                distrib[category]=distrib[category]+1
            else:
                distrib[category]=1

        self.assert_(distrib['auto burglary']==12)
        self.assert_(distrib['grand theft']==5)
        self.assert_(distrib['suspicious circumstances']==10)
        self.assert_(distrib['domestic disturbance']==4)
        self.assert_(distrib['battery']==5)
        self.assert_(distrib['commercial burglary']==2)
        self.assert_(distrib['residential burglary']==5)
        self.assert_(distrib['vandalism']==13)
        self.assert_(distrib['robbery']==4)
        self.assert_(distrib['assault']==1)
        self.assert_(distrib['stolen vehicle']==9)


    def test_populate_db_issue_000038(self):
        """
        parse issue #38 police log, stuff into database"""

        #
        # set up database
        issue_num=38
        police_log=PoliceLog(issue_number=issue_num,
                             issue_exists=True,
                             pub_date=datetime.date(2006,3,10))
        police_log.save()

        #
        # associate db entry with 
        # log file in test directory 
        test_dir=TEST_DATA_IN
        findpolicelog.sync_download_issue_with_db(issue_num,test_dir)

        # 
        # parse crime log and load crimes into db
        p=parsepolicelog.PoliceLogParser(test_dir)
        p.parse_log_and_populate_db(issue_num,issue_num)

        #
        # should be 70 crime reports associated with 000038
        # the following query set is equivalent to:
        #   police_log=PoliceLog.objects.get(issue_number__exact=issue_num)
        #   crime_report_list=police_log.crimereport_set.all()
        crime_report_list=CrimeReport.objects.filter(policelog__issue_number__exact=issue_num)
        
        self.assert_(len(crime_report_list)==70)

        if False:
            for crime_report in crime_report_list:
                print "%d %d  %s (%s)" % (crime_report.category,
                                          crime_report.line_num,
                                          crime_report.address,
                                          mapscale.dict[crime_report.map_scale])

        #
        # parse_and_populate_db shouldn't have created an issue 39
        try:
            police_log = PoliceLog.objects.get(issue_number__exact=issue_num+1)
        except PoliceLog.DoesNotExist:
            pass
            

        #
        # check distribution of parsed crimes
        category_distrib=get_crime_type_distribution(crime_report_list)
        scale_distrib=get_mapscale_distribution(crime_report_list)

        self.assert_(category_distrib['auto burglary']==12)
        self.assert_(category_distrib['grand theft']==5)
        self.assert_(category_distrib['suspicious circumstances']==10)
        self.assert_(category_distrib['domestic disturbance']==4)
        self.assert_(category_distrib['battery']==5)
        self.assert_(category_distrib['commercial burglary']==2)
        self.assert_(category_distrib['residential burglary']==5)
        self.assert_(category_distrib['vandalism']==13)
        self.assert_(category_distrib['robbery']==4)
        self.assert_(category_distrib['stolen vehicle']==9)
        self.assert_(category_distrib['assault']==1)

        self.assert_(scale_distrib[mapscale.BLOCK]==56)
        self.assert_(scale_distrib[mapscale.INTERSECTION]==1)
        self.assert_(scale_distrib[mapscale.EXACT]==2)
        self.assert_(scale_distrib[mapscale.OTHER]==11)


    def test_populate_db_issue_000039(self):
        """
        parse issue #39 police log, stuff into database"""

#         #
#         # set up database
        issue_num=39
#         police_log=PoliceLog(issue_number=issue_num,
#                              issue_exists=True,
#                              pub_date=datetime.date(2006,3,10))
#         police_log.save()

#         #
#         # associate db entry with 
#         # log file in test directory 
#         test_dir=TEST_DATA_IN
#         findpolicelog.sync_download_issue_with_db(issue_num,test_dir)

#         # 
#         # parse crime log and load crimes into db
#         p=parsepolicelog.PoliceLogParser(test_dir)
#         p.parse_log_and_populate_db(issue_num,issue_num)

        #
        # 
        #police_log=PoliceLog.objects.get(issue_number__exact=issue_num)
        #crime_report_list=police_log.crimereport_set.all()
        crime_report_list=CrimeReport.objects.filter(policelog__issue_number__exact=issue_num)
        
        #
        # check distribution of parsed crimes
        category_distrib=get_crime_type_distribution(crime_report_list)
        scale_distrib=get_mapscale_distribution(crime_report_list)


        self.assert_(category_distrib['vandalism']==5)
        self.assert_(category_distrib['robbery']==1)
        self.assert_(category_distrib['grand theft']==6)
        self.assert_(category_distrib['battery']==7)
        self.assert_(category_distrib['stolen vehicle']==8)
        self.assert_(category_distrib['commercial burglary']==3)
        self.assert_(category_distrib['suspicious circumstances']==12)
        self.assert_(category_distrib['residential burglary']==3)
        self.assert_(category_distrib['domestic disturbance']==5)
        self.assert_(category_distrib['auto burglary']==12)


        self.assert_(scale_distrib[mapscale.BLOCK]==52)
        self.assert_(scale_distrib[mapscale.INTERSECTION]==7)
        self.assert_(scale_distrib[mapscale.OTHER]==3)

        if False:
            for crime_report in crime_report_list:
                print "%d %d %d  %s (%s)" % (crime_report.issue_number.issue_number,
                                             crime_report.category,
                                          crime_report.line_num,
                                          crime_report.address,
                                          mapscale.dict[crime_report.map_scale])


    def test_parse_000039_00(self):
        line='''<p class=story_text>700 block San Pablo, 1/30<P></p>'''
        
        p=parsepolicelog.PoliceLogParser()
        crime_report=p.parse_report_line(line)
        self.assert_(crime_report['map_scale']==mapscale.BLOCK)

    def test_parse_000039_01(self):
        line='''<p class=story_text>Moffett Blvd./Stevens Creek, 1/30<P></p>'''

        p=parsepolicelog.PoliceLogParser()
        crime_report=p.parse_report_line(line)
        self.assert_(crime_report['map_scale']==mapscale.INTERSECTION)


#     def test_populate_db_issue_000040(self):
#         """
#         parse issue #39 police log, stuff into database"""

#         #
#         # set up database
#         issue_num=40
#         police_log=PoliceLog(issue_number=issue_num,
#                              issue_exists=True,
#                              pub_date=datetime.date(2006,3,10))
#         police_log.save()

#         #
#         # associate db entry with 
#         # log file in test directory 
#         test_dir=TEST_DATA_IN
#         findpolicelog.sync_download_issue_with_db(issue_num,test_dir)

#         # 
#         # parse crime log and load crimes into db
#         p=parsepolicelog.PoliceLogParser(test_dir)
#         p.parse_log_and_populate_db(issue_num,issue_num)

#         #
#         # this is equivalent to this:
#         #         police_log=PoliceLog.objects.get(issue_number__exact=issue_num)
#         #         crime_report_list=police_log.crimereport_set.all()
#         crime_report_list=CrimeReport.objects.filter(policelog__issue_number__exact=issue_num)
        
#         #
#         # check distribution of parsed crimes
#         category_distrib=get_crime_type_distribution(crime_report_list)
#         scale_distrib=get_mapscale_distribution(crime_report_list)


#         if False:
#             for crime_report in crime_report_list:
#                 print "%d %s %d  %s (%s)" % (crime_report.policelog.issue_number,
#                                              crime_report.category,
#                                           crime_report.line_num,
#                                           crime_report.address,
#                                           crime_report.map_scale)

    def test_crimereport_unique_hash(self):
        """
        verify that crimereport hash prevents duplicate crime report entries in db"""

        #
        # set up database
        issue_num=39
#         police_log=PoliceLog(issue_number=issue_num,
#                              issue_exists=True,
#                              pub_date=datetime.date(2006,3,10))
#         police_log.save()

#         #
#         # associate db entry with 
#         # log file in test directory 
        test_dir=TEST_DATA_IN
#         findpolicelog.sync_download_issue_with_db(issue_num,test_dir)

#         # 
#         # parse crime log and load crimes into db
#         p=parsepolicelog.PoliceLogParser(test_dir)
#         p.parse_log_and_populate_db(issue_num,issue_num)

        #
        # count entries in db
        crime_report_list=CrimeReport.objects.filter(policelog__issue_number__exact=issue_num)
        num_reports1=len(crime_report_list)


        # 
        # parse crime log and load crimes into db AGAIN
        p=parsepolicelog.PoliceLogParser(test_dir)
        p.parse_log_and_populate_db(issue_num,issue_num)
        crime_report_list=CrimeReport.objects.filter(policelog__issue_number__exact=issue_num)
        num_reports2=len(crime_report_list)
        
        #
        # verify that second parse_log_and_populate_db didn't result
        # in additional db entries
        self.assert_(num_reports1==num_reports2)

class TestMvGeocoder(unittest.TestCase):
    def setUp(self):
        pass


    def test_geocode_block_address(self):
        """
        try to geocode a known address"""
        crime_report=CrimeReport()
        crime_report.address='300 block mountain view ave.'
        crime_report.map_scale=mapscale.BLOCK
        
        geocoder=MvGeocoder()
        (lat,long)=geocoder.geocode(crime_report.address,crime_report.map_scale)

        self.assert_(lat=='37.3947668')
        self.assert_(long=='-122.0853018')

    def test_geocode_bad_address(self):
        """
        bad addresses should be geocoded with invalid lat,long values"""

        crime_report=CrimeReport()
        crime_report.address='publix'   # ain't no publix in MV, dumbass
        crime_report.map_scale=mapscale.BLOCK
        
        geocoder=MvGeocoder()
        (lat,long)=geocoder.geocode(crime_report.address,crime_report.map_scale)

        self.assert_(lat==str(geocoder.INVALID_LAT))
        self.assert_(long==str(geocoder.INVALID_LONG))

    def test_geocode_addr_38_1(self):
        """
        test geocoding of problem address from issue 38"""

        crime_report=CrimeReport()
        crime_report.address='1200 block Cuernavaca Cl.'   # circulo
        crime_report.map_scale=mapscale.BLOCK
        
        geocoder=MvGeocoder()
        (lat,long)=geocoder.geocode(crime_report.address,crime_report.map_scale)
        self.assert_(lat=='37.3716608')
        self.assert_(long=='-122.0640654')

    def test_geocode_addr_38_2(self):
        """
        test geocoding of problem address from issue 38

        800 block el camino real:
        geocoding fails in this case because the address doesnt specify east or west ECR
        proper response is to return INVALID_LAT,INVALID_LONG"""

        crime_report=CrimeReport()
        crime_report.address='800 block el camino real'
        crime_report.map_scale=mapscale.BLOCK
        
        geocoder=MvGeocoder()
        (lat,long)=geocoder.geocode(crime_report.address,crime_report.map_scale)
        self.assert_(lat==str(geocoder.INVALID_LAT))
        self.assert_(long==str(geocoder.INVALID_LONG))


    def test_geocode_and_write_db(self):
        """
        try to geocode a known address
        and write results back into db"""
        crime_report=CrimeReport()
        crime_report.address='300 block mountain view ave.'
        crime_report.map_scale=mapscale.BLOCK
        
        geocoder=MvGeocoder()
        (lat,long)=geocoder.geocode(crime_report.address,crime_report.map_scale)

        self.assert_(lat=='37.3947668')
        self.assert_(long=='-122.0853018')

