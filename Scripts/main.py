
import pandas as pd
from SEC.SEC_scraper import CIKLookup
from SEC.financials_manager import Financials


#simple script that'll download all tickers
#and all the associated SEC files
def download_all_files():
    lookup = CIKLookup()
    src = './SEC_files/Ticker'
    cik_data = lookup.get_all_CIK()
    for ind,cik in enumerate(cik_data['CIK']):
        ticker = cik_data['ticker'][ind]
        print('Working on...',ticker)
        data = Financials().get_financials(cik)
        df = pd.DataFrame(data)
        df.to_csv(src+'/'+ticker+'.csv')
        print("Completed")

def update_ticker():

    return

def download_file(ticker=''):
    if len(ticker) == 0: return
    src = './SEC_files/Ticker'
    cik_data = CIKLookup().CIK_lookup(ticker=ticker)
    print('Working on...',ticker)
    data = Financials().get_financials(cik_data)
    df = pd.DataFrame(data)
    df.to_csv(src+'/'+ticker+'.csv')
    print("Completed")

    



#for testing purposes
if __name__ == '__main__':
    download_file('GOOGL')