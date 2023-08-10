import pandas as pd
import requests
import time
from datetime import datetime
from bs4 import BeautifulSoup as BS

time_of_last_request = datetime(2000,1,1)
#Financials Manager, to download,search,query using the SEC_scraper
class Financials():

    def get_header(self):
        header = {
            'User-agent':'Jack Wong jackbwong1998@gmail.com',
            }
        return header
    def get_financials(self,CIK):
        temp = self.lookup(CIK)
        if(not temp.empty):
            temp2=self.get10k_links(CIK,temp)
            if(temp2!=None):
                temp3=self.getFinancials_from_links(temp2)
                if(temp3!=None):
                    return temp3
        return None
    
    #retrieve raw data as dataframe from company/CIK
    def lookup(self,CIK):
        try:
            CIK = str(CIK).zfill(10)
            data = self.throttle_request('https://data.sec.gov/submissions/CIK'+CIK+'.json').json()

            #gathers recent data
            df = pd.DataFrame(data['filings']['recent'])

            #gathers historical Data
            data = self.throttle_request('https://data.sec.gov/submissions/'+data['filings']['files'][0]['name']).json()
            df2 = pd.DataFrame(data)

            df = pd.concat([df,df2],ignore_index=True)
            return df

        except Exception as e:
            print(e)
            return None

    #retrieves 10-k links from the DF
    def get10k_links(self,cik,df):
        data = df.loc[df['primaryDocDescription'].str.contains('10-K')==True]
        ret = {'raw':[],'readable':[],'cik':[],'accessionNumber':[],'filingDate':[]}

        for row in data.index:
            if(data['primaryDocument'][row] == ''): continue
            accessionNumber = data['accessionNumber'][row]
            document = data['primaryDocument'][row]
            filingDate = data['filingDate'][row]

            readable_link = 'https://www.sec.gov/ix?doc=/Archives/edgar/data/'+str(cik)+'/'+accessionNumber.replace('-','')+'/'+document
            raw_link = 'https://www.sec.gov/Archives/edgar/data/'+str(cik)+'/'+accessionNumber.replace('-','')+'/'+accessionNumber+'.txt'

            ret['raw'].append(raw_link)
            ret['readable'].append(readable_link)
            ret['cik'].append(cik)
            ret['accessionNumber'].append(accessionNumber)
            ret['filingDate'].append(filingDate)


        return ret


    #to be within the standards of SEC requests we can only request information
    #10 times per second
    def throttle_request(self,link):
        global time_of_last_request
        if(datetime.now().microsecond-time_of_last_request.microsecond<100):
            time.sleep(.1)
        time_of_last_request = datetime.now()

        return requests.get(link,headers=self.get_header())

    def getFinancials_from_links(self,links):
        data = {}
        for ind,link in enumerate(links['raw']):
            html_text = self.throttle_request(link).content


            year = datetime.strptime(str(links['filingDate'][ind]),'%Y-%m-%d').year
            company = self.get_company_name(html_text)
            revenue = self.get_revenue(html_text)
            net_income = self.get_net_income(html_text)
            diluted_shares = self.get_diluted_shares(html_text)
            cash_and_cash_equivalent = self.get_cash_and_cash_equivalent(html_text)
            current_and_long_term_debt = self.get_current_and_long_term_debt(html_text)
            long_term_assets = self.get_long_term_assets(html_text)
            depreciation_and_amortization = self.get_depreciation_and_amortization(html_text)


            if(revenue != None):
                for ind2,result in enumerate(revenue):
                    if(year-ind2) in data:
                        data[year-ind2]['revenue'] = result
                    else:
                        data[year-ind2] = {'year':year-ind2, 
                                           'company':company,
                                      'revenue':result}


            if(net_income != None):
                for ind2,result in enumerate(net_income):
                    if(year-ind2) in data:
                        data[year-ind2]['net_income'] = result
                    else:
                        data[year-ind2] = {'year':year-ind2, 
                                           'company':company,
                                      'net_income':result}
            if(diluted_shares != None):
                for ind2,result in enumerate(diluted_shares):
                    if(year-ind2) in data:
                        data[year-ind2]['diluted_shares'] = result
                    else:
                        data[year-ind2] = {'year':year-ind2, 
                                           'company':company,
                                      'diluted_shares':result}
            if(cash_and_cash_equivalent != None):
                for ind2,result in enumerate(cash_and_cash_equivalent):
                    if(year-ind2) in data:
                        data[year-ind2]['cash_and_cash_equivalent'] = result
                    else:
                        data[year-ind2] = {'year':year-ind2, 
                                           'company':company,
                                      'cash_and_cash_equivalent':result}

            if(current_and_long_term_debt != None):
                for ind2,result in enumerate(current_and_long_term_debt):
                    if(year-ind2) in data:
                        data[year-ind2]['current_and_long_term_debt'] = result
                    else:
                        data[year-ind2] = {'year':year-ind2, 
                                           'company':company,
                                      'current_and_long_term_debt':result}

            if(long_term_assets != None):
                for ind2,result in enumerate(long_term_assets):
                    if(year-ind2) in data:
                        data[year-ind2]['long_term_assets'] = result
                    else:
                        data[year-ind2] = {'year':year-ind2, 
                                           'company':company,
                                      'long_term_assets':result}


            if(depreciation_and_amortization != None):
                for ind2,result in enumerate(depreciation_and_amortization):
                    if(year-ind2) in data:
                        data[year-ind2]['depreciation_and_amortization'] = result
                    else:
                        data[year-ind2] = {'year':year-ind2, 
                                           'company':company,
                                      'depreciation_and_amortization':result}



            else:
                print('Error finding Financials\nReadable:',links['readable'][ind],'\nRaw:',links['raw'][ind])
                print("needs to be fined tuned, this will not be done here")
                break
            print('COMPLETED readable link:',links['readable'][ind])



        if(len(data.keys())==0):
            return None
        return data

    def get_company_name(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonnumeric':{'name':['dei:EntityRegistrantName']},
                }
            soup = BS(html_text,'lxml')
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        return soup.find(tag,attrs={key:value}).text
            return None


        except Exception as e:
            print(e)
            return None



    def get_revenue(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonfraction':{'name':['us-gaap:Revenues','us-gaap:RevenueFromContractWithCustomerExcludingAssessedTax']},
                }
            soup = BS(html_text,'lxml')
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        revenue = soup.find_all('ix:nonfraction',attrs={key:value})
                        if(len(revenue)!=0):
                            return [(str(revenue[0].text)+''.zfill(abs(int(revenue[0]['decimals'])))).replace(',',''),
                                    (str(revenue[1].text)+''.zfill(abs(int(revenue[1]['decimals'])))).replace(',',''),
                                    (str(revenue[2].text)+''.zfill(abs(int(revenue[2]['decimals'])))).replace(',','')]                                    
            return None

        except Exception as e:
            print(e)
            return None





    def get_net_income(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonfraction':{'name':['us-gaap:NetIncomeLoss']},
                }
            soup = BS(html_text,'lxml')
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        result = soup.find_all('ix:nonfraction',attrs={key:value})
                        if(len(result)!=0):
                            return [(str(result[0].text)+''.zfill(abs(int(result[0]['decimals'])))).replace(',',''),
                                    (str(result[1].text)+''.zfill(abs(int(result[1]['decimals'])))).replace(',',''),
                                    (str(result[2].text)+''.zfill(abs(int(result[2]['decimals'])))).replace(',','')]                                    
            return None

        except Exception as e:
            print(e)
            return None

    def get_diluted_shares(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonfraction':{'name':['us-gaap:EarningsPerShareDiluted']},
                #or use us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding
                #for shared outstanding
                }
            soup = BS(html_text,'lxml')
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        result = soup.find_all('ix:nonfraction',attrs={key:value})
                        if(len(result)!=0):
                            return [(str(result[0].text)),
                                    (str(result[1].text)),
                                    (str(result[2].text))]                                    
            return None

        except Exception as e:
            print(e)
            return None


    def get_cash_and_cash_equivalent(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonfraction':{'name':['us-gaap:CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents']},
                #or use us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding
                #for shared outstanding
                }
            soup = BS(html_text,'lxml')
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        result = soup.find_all('ix:nonfraction',attrs={key:value})
                        result = result[-3:]
                        if(len(result)!=0):
                            return [(str(result[0].text)+''.zfill(abs(int(result[0]['decimals'])))).replace(',',''),
                                    (str(result[1].text)+''.zfill(abs(int(result[1]['decimals'])))).replace(',',''),
                                    (str(result[2].text)+''.zfill(abs(int(result[2]['decimals'])))).replace(',','')]                                      
            return None

        except Exception as e:
            print(e)
            return None

    def get_current_and_long_term_debt(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonfraction':{'name':['us-gaap:LiabilitiesCurrent','us-gaap:LongTermDebtNoncurrent']},
                #or use us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding
                #for shared outstanding
                }
            soup = BS(html_text,'lxml')
            ret = [0,0]
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        result = soup.find_all('ix:nonfraction',attrs={key:value})
                        if(len(result)!=0):
                            ret[0] = ret[0]+int(result[0].text.replace(',','')+''.zfill(abs(int(result[0]['decimals']))))
                            ret[1] = ret[1]+int(result[1].text.replace(',','')+''.zfill(abs(int(result[1]['decimals']))))

            if(ret[0]!=0):
                return ret                             
            return None

        except Exception as e:
            print(e)
            return None


    def get_long_term_assets(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonfraction':{'name':['us-gaap:Assets','us-gaap:AssetsCurrent']},
                #or use us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding
                #for shared outstanding
                }
            soup = BS(html_text,'lxml')
            ret = [0,0]
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        result = soup.find_all(tag,attrs={key:value})
                        if(len(result)!=0):
                            if(value == 'us-gaap:Assets'):
                                ret[0] = ret[0]+int(result[0].text.replace(',','')+''.zfill(abs(int(result[0]['decimals']))))
                                ret[1] = ret[1]+int(result[1].text.replace(',','')+''.zfill(abs(int(result[1]['decimals']))))
                            else:
                                ret[0] = ret[0]-int(result[0].text.replace(',','')+''.zfill(abs(int(result[0]['decimals']))))
                                ret[1] = ret[1]-int(result[1].text.replace(',','')+''.zfill(abs(int(result[1]['decimals']))))

            if(ret[0]!=0):
                return ret                             
            return None

        except Exception as e:
            print(e)
            return None
    def get_depreciation_and_amortization(self,html_text):
        try:
            keyphrases = {
                #dictionary that should contain keywords for revenue
                #should be in this format
                #TAG:['keyword1', 'keyword2', 'keyword3']
                #such that TAG is the identifying tag which can be div, p1,h1,table, etc.
                #second is the name that is associated with it such that it can be........
                #class='revenue_of_company_XYZ'
                #then it should be stored as 'class':['revenue_of_company_XYZ',]
                'ix:nonfraction':{'name':['us-gaap:DepreciationDepletionAndAmortization','us-gaap:DepreciationAndAmortization']},
                #or use us-gaap:WeightedAverageNumberOfDilutedSharesOutstanding
                #for shared outstanding
                }
            soup = BS(html_text,'lxml')
            ret = [0,0]
            for tag in keyphrases:
                for key in keyphrases[tag]:
                    for value in keyphrases[tag][key]:
                        result = soup.find_all(tag,attrs={key:value})
                        if(len(result)!=0):

                            return [int(result[0].text.replace(',','')+''.zfill(abs(int(result[0]['decimals'])))),
                                    int(result[1].text.replace(',','')+''.zfill(abs(int(result[0]['decimals'])))),
                                    int(result[2].text.replace(',','')+''.zfill(abs(int(result[0]['decimals'])))),]


            if(ret[0]!=0):
                return ret                             
            return None

        except Exception as e:
            print(e)
            return None

    

if __name__ == '__main__':
    test = Financials()



