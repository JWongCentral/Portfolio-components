import pandas as pd
import numpy as np
import yfinance as yf
import os

class processing_data():
    
    
    def __init__(self, ticker = [], src = './Portfolio-components/SEC_files/Ticker'):
        self.src = src
        return
    
    #this will combine all the information into one file for easier training
    def combine_data(self, src=''):
        ret = pd.DataFrame()
        for file in os.listdir(self.src):
            data = pd.read_csv(self.src+'/'+file,index_col=0)
            ticker = file.replace('.csv','')
            data['ticker']=ticker
            data = data.rename({'Unnamed: 0':'Variable'},axis='columns')
            data.insert(0,'ticker',data.pop('ticker'))
            print(data.head())
            break

        return

        

if __name__ == "__main__":
    test = processing_data()
    test.combine_data()



