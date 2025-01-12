import pandas as pd
import os
from flask import current_app
import csv
ressources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'resources')

def load_categories(file_path):
    with open(os.path.join(ressources_dir,file_path), 'r') as file:
        lines = file.readlines()

    categories = {}
    current_category = None

    for line in lines:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if line.startswith(' '):  # Assuming sub-categories are indented
            if current_category:
                categories[current_category].append(stripped_line)
        else:
            current_category = stripped_line
            categories[current_category] = []
    return categories

def save_global(dataframe,file): #TODO remove duplicate functions with overview
    dataframe['Buchungsdatum'] = pd.to_datetime(dataframe['Buchungsdatum'])
    dataframe['Buchungsdatum']=dataframe['Buchungsdatum'].dt.strftime('%d-%m-%Y')
    dataframe.to_csv(os.path.join(ressources_dir,file), index=False)
    return

#def load_data(file1):
#    if os.path.exists(os.path.join(ressources_dir,file1)):
#        df = pd.read_csv(os.path.join(ressources_dir,file1), sep=';') #TO>DO put file in ressources directory. See in edit as well
#    return df

def load_account_data(file3): #config.txt
    account_data = {}
    file_path = os.path.join(ressources_dir, file3)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"File {file3} does not exist.")
        return 0  # Return 0 if the file does not exist

    # Process the file if it exists
    with open(file_path, mode='r') as file:
        reader = csv.reader(file,delimiter=';')
        #next(reader)  # Skip the header row if there is one
        for row in reader:
            account_code = row[0]
            account_name = row[1]
            account_value = float(row[2])  # Assuming the value column contains numeric data
            account_data[account_code] = {'name': account_name, 'value': account_value}
    return account_data

def detect_transfers(row):
    if row['Konto']=='{postbank_account}':
        if row['Kategorie']=='PayPal':
            row['Kategorie']='Umbuchung'
        if row['Umbuchung']=='0-Euro-Konto':
            row['Kategorie']='Umbuchung'
        if row['Buchungstext']=='LASTSCHRIFT':      
            row['Kategorie']='Umbuchung' 
    if row['Konto']=='{commerzbank_account}':
        if row['Umbuchung']=='Postbank Giro extra plus':
            row['Kategorie']='Umbuchung'
    if row['Konto']=='PayPal (albanatita@gmail.com)':
        if row['Kategorie']=='Sonstige Einnahmen':
            row['Kategorie']='Umbuchung'
    return row['Kategorie']

    df['Month'] = df['Buchungsdatum'].dt.to_period('M')
    return df

def load_data(file):
        df = pd.read_csv(os.path.join(ressources_dir,file),sep=',')
        df['Buchungsdatum'] = pd.to_datetime(df['Buchungsdatum'], format='%d-%m-%Y')
        #df['Betrag'] = pd.to_numeric(df['Betrag'].replace(',','.',regex=True), errors='coerce')
        return df

def merge_new_data(file1, file2):
    try:
        df_existing = pd.read_csv(os.path.join(ressources_dir,file2),sep=',') #todo merge with load_data
        df_existing['Buchungsdatum'] = pd.to_datetime(df_existing['Buchungsdatum'])#, format='%d.%m.%Y')
        df_existing['Betrag'] = pd.to_numeric(df_existing['Betrag'].replace(',','.',regex=True), errors='coerce')
        df_existing=df_existing[['Buchungsdatum','Empfaenger','Verwendungszweck','Buchungstext','Betrag','IBAN','Kategorie','Konto','Umbuchung','Notiz','Schlagworte','Month','Saldo']]
        df_existing['Kategorie'] = df_existing.apply(detect_transfers, axis=1) 
        if 'Month' not in df_existing.columns:
            df_existing['Month']=0
        if 'Saldo' not in df_existing.columns:
            df_existing['Saldo']=0
        df_existing['Buchungsdatum']=df_existing['Buchungsdatum'].dt.strftime('%d-%m-%Y')
    except Exception as e:
        print('File note found')
        return {'code': 0, 'msg':  str(e) + ' - '+os.path.join(ressources_dir,file2)}
   # Load the CSV with additional rows-
    try:
        df_new = pd.read_csv(os.path.join(ressources_dir,file1))
    except FileNotFoundError as e:
        return {'code': 1, 'msg': 'No update of transactions found, just loading existing file', 'data':df_existing}
    df_new['Betrag'] = pd.to_numeric(df_new['Betrag'].replace(',','.',regex=True), errors='coerce')
    df_new = df_new[['Buchungsdatum','EMpfaenger','Verwendungszweck','Buchungstext','Betrag','IBAN','Kategorie','Konto','Umbuchung','Notiz','Schlagworte','Month','Saldo']]
    df_new['Month']=[]
    df_new['Saldo']=[]
    df_new['Buchungsdatum'] = pd.to_datetime(df['Buchungsdatum'], format='%d.%m.%Y')
    df_new['Kategorie'] = df_new.apply(detect_transfers, axis=1)  
    # Concatenate the existing DataFrame and new data
    df_combined = pd.concat([df_existing, df_new])
    # Drop duplicates based on only three columns (replace 'column1', 'column2', 'column3' with actual column names)
    df_combined = df_combined.drop_duplicates(subset=['Buchungsdatum', 'Verwendungszweck', 'Empfaenger','IBAN','Konto'])
    df_combined['Buchungsdatum']=df_combined['Buchungsdatum'].dt.strftime('%d-%m-%Y')
    # Save the updated DataFrame (if needed)
    #df_combined.to_csv(os.path.join(ressources_dir,file2))
    return {'code':1,'msg':'Account data file update', 'data': df_combined}


 
def pivot_table(file4,df):
    # Predefined list of categories
    categories = load_categories(os.path.join(ressources_dir,file4))
    category_order = []
    for sublist in categories.values():
        category_order.extend(sublist)
    df['Buchungsdatum'] = pd.to_datetime(df['Buchungsdatum'], format='%d-%m-%Y')
    df['Month']=df['Buchungsdatum'].dt.month
    #df['Betrag'] = pd.to_numeric(df['Betrag'].str.replace(',', '.'))
    # Set the category order
    df['Kategorie'] = pd.Categorical(df['Kategorie'], categories=category_order, ordered=True)
    pivot_table = df.pivot_table(values='Betrag', index='Kategorie', columns='Month', aggfunc='sum', fill_value=0)
    pivot_table.columns = pivot_table.columns.astype(str)  # Convert Period to str
    pivot_table = pivot_table.reindex(category_order)  # Reindex to enforce the order
#    for col in pivot_table.select_dtypes(include=['float', 'int']).columns:
#        pivot_table[col] = pivot_table[col].map('{:.2f}'.format)
    return pivot_table



def load_budget(file):
    file_path=os.path.join(ressources_dir,file)
    # Load existing data if the file exists
    if os.path.exists(file_path):
        df = pd.read_csv(file_path,sep=',',skiprows=1)
        df.columns=['type', 'datetype', 'description', 'amount', 'account']
    else:
        df = pd.DataFrame(columns=['type', 'datetype', 'description', 'amount', 'account'])
    return df

def save_budget(file1,file2, df1, df2):
        file1_path=os.path.join(ressources_dir,file1)
        file2_path=os.path.join(ressources_dir,file2)
        df1.to_csv(file1_path, index=False)
        df2.to_csv(file2_path, index=False)
        return

def load_occurences(file1):
        file1_path=os.path.join(ressources_dir,file1)
        df = pd.read_csv(file1_path)
        df['date']=pd.to_datetime(df['date'], format='%d-%m-%Y')
        return df