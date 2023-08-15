#For MongoDB Purposes
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import pandas as pd
import os
uri = 'SECRET'
client = None

def open_connection():
    global client
    client = MongoClient(uri, server_api=ServerApi('1'))
    test_mongodb_server()

def close_connection():
    global client
    print('Client Closed:',client.close()==None)

def test_mongodb_server():
    # Create a new client and connect to the server
    global client
    # Send a ping to confirm a successful connection
    try:
        client.admin.command('ping')
        print("Pinged your deployment. You successfully connected to MongoDB!")
    except Exception as e:
        print(e)


#this will perform the create/update functionality
#The entry will be a dict containing the name of the company AND the year amongst the financial data
#it will then add
def add_entry(entry):
    global client
    db = client['SEC']
    #creating collection if it does not exist
    if not (entry['year'] in db.list_collection_names()):
        db.create_collection(entry['year'])
    
    collection = db[entry['year']]

    #query and check if it exists if not we will add
    query = {'ticker':entry['ticker'], 'year':entry['year']}
    document = collection.find_one(query)

    #exists so we will check if we need to update
    if document:
        for field in entry.keys():
            if (document[field]!=entry[field]):
                collection.update_one(query, {'$set':entry})
                return True
        
    #does not exist so we will add
    else:
        collection.insert_one(entry)
        return True
    


#This will look into the SEC_Financials to look for the ticker.csv
#then it will add each individual entry to the collection
def add_ticker(ticker='',src='./SEC_files/Ticker'):
    
    if not os.path.exists(src+'/'+ticker+'.csv') or ticker=='':
        return False
    
    file = pd.read_csv(src+'/'+ticker.capitalize()+'.csv', index_col=0).to_dict()
    for i in file:
        file[i]['year']=i
        file[i]['ticker']=ticker
        file[i]['_id']= ticker+'-'+i
        add_entry(file[i])
        
    return True


def delete_from_sec_db():
    global client
    db = client['SEC']
    return True

def update_all_financials(src='./SEC_files/Ticker'):
    for i in os.listdir(src):
        add_ticker(ticker=i.replace('.csv',''))
    return True





#for testing purposes
if __name__ == "__main__":
    open_connection()
    print(update_all_financials())


    close_connection()