import functions
import pandas as pd
import os
import csv
ressources_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),'resources')


file0='non_processed.csv'
file1='accounts.txt'
file2='processed.csv'
file3='config.txt'
file4='categories.txt'
file5='budget.txt'
file6='occurences.csv'
file7='new_categories.txt'
file8='pivot.csv'
file9='fraisfixes.txt'

print('1 - Loading data')
df_existing = pd.read_csv(os.path.join(ressources_dir,file0),sep=';') #todo merge with load_data
df_existing['Buchungsdatum'] = pd.to_datetime(df_existing['Buchungsdatum'], format='%d.%m.%Y')
df_existing['Betrag'] = pd.to_numeric(df_existing['Betrag'].replace(',','.',regex=True), errors='coerce')
df_existing['Betrag']=df_existing['Betrag'].astype(float)
df_existing=df_existing[['Buchungsdatum','Empfaenger','Verwendungszweck','Buchungstext','Betrag','IBAN','Kategorie','Konto','Umbuchung','Notiz','Schlagworte']]
df_existing['Kategorie'] = df_existing.apply(functions.detect_transfers, axis=1) 
df_existing['Month']=df_existing['Buchungsdatum'].dt.month
df_existing['Saldo']=0
df=df_existing

print('2- Calculating saldo')
rows = pd.read_csv(os.path.join(ressources_dir,file1),header=0,sep=';')
# Ensure that the 'date' column is in datetime format (if not already)
rows['Date'] = pd.to_datetime(rows['Date'], format='%d-%m-%Y')
# Create a dictionary in the desired format
account_dict = {
    row['Account']: {'date': row['Date'], 'saldo': row['Saldo']}
    for _, row in rows.iterrows()
}


initial_date=date = rows ['Date'][0] # to modify after in the accounts file
df_calc=df[df['Buchungsdatum']>=initial_date].sort_values(by='Buchungsdatum', ascending=True)

def calculate_saldo(group, initial_saldo):
    group['Saldo'] = initial_saldo + group['Betrag'].cumsum()
    return group

df = df_calc.groupby('Konto', group_keys=False).apply(lambda g: calculate_saldo(g, account_dict[g.name]['saldo']))


print('3 - Calculating occurences')
data=functions.load_budget(file5).to_dict('records')
occurrences = []
for row in data:
    type_ = int(row['type'])
    datetype = pd.to_datetime(row['datetype'],dayfirst=True)
    description = row['description']
    amount = row['amount']
    account = row['account']

    if type_ == 0:
        occurrences.append({
            'date': datetype.strftime('%d-%m-%Y'),
            'amount': str(amount),
            'description': description,
            'account': account
        })
    elif type_ == 1:
        for i in range(12):
            new_date = (datetype + pd.DateOffset(months=i)).strftime('%d-%m-%Y')
            occurrences.append({
                'date': new_date,
                'amount': str(amount),
                'description': description,
                'account': account
            })
    elif type_ == 2:

        for i in range(0, 12, 3):
            new_date = (datetype + pd.DateOffset(months=i)).strftime('%d-%m-%Y')
            occurrences.append({
                'date': new_date,
                'amount': str(amount),
                'description': description,
                'account': account
            })
    elif type_ == 3:
        new_date = datetype
        occurrences.append({
            'date': new_date.strftime('%d-%m-%Y'),
            'amount': str(amount),
            'description': description,
            'account': account
        })
occ= pd.DataFrame(occurrences)
file2_path=os.path.join(ressources_dir,file6)
occ.to_csv(file2_path, index=False)

def categorize_spending(receiver, description, categories,default='Uncategorized'):
    # Combine receiver and description for keyword search
    combined_text = f"{receiver.lower()} {description.lower()}"

    # Iterate through categories and their keywords
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in combined_text:
                return category
    
    # Default category if no keywords match
    return default

print('3bis - Frais fixes')
file9_path=os.path.join(ressources_dir,file9)
with open(file9_path, 'r') as file:
    keywords={}   
    for line in file:
        stripped_line = line.strip()
        category, kw = stripped_line.split(':')
        keywords[category.strip()] = [k.strip().lower() for k in kw.split(',')]
keywords={k: v for k, v in keywords.items() if v != ['']}

df['Notiz'] = df.apply(lambda x: categorize_spending(str(x['Empfaenger']), str(x['Verwendungszweck']), keywords,default='-'), axis=1)


print('4 - New categorizing')
file7_path=os.path.join(ressources_dir,file7)

with open(file7_path, 'r') as file:
    keywords = {}
    all_categories=[]
    categories={}
    for line in file:
        stripped_line = line.strip()
        if not stripped_line:
            continue
        if line.startswith(' '):  # Assuming sub-categories are indented
            if current_category:
                        # Split the line into category and keywords
                category, kw = stripped_line.split(':')
                # Strip whitespace and split keywords by comma
                keywords[category.strip()] = [k.strip().lower() for k in kw.split(',')]
                categories[current_category].append(category.strip())
                all_categories.append(category.strip())
        else:
            current_category = stripped_line
            categories[current_category] = []
keywords={k: v for k, v in keywords.items() if v != ['']}


df['Category'] = df.apply(lambda x: categorize_spending(str(x['Empfaenger']), str(x['Verwendungszweck']), keywords), axis=1)
print('Total number of elements: '+str(df.shape[0]))
print('Uncategorized: '+str(df[df['Category']=='Uncategorized'].shape[0]))

df['Buchungsdatum'] = pd.to_datetime(df['Buchungsdatum'])
df['Buchungsdatum']=df['Buchungsdatum'].dt.strftime('%d-%m-%Y')
df.to_csv(os.path.join(ressources_dir,file2),index=False)

print('5 - creating pivot table for categories')

df['Buchungsdatum'] = pd.to_datetime(df['Buchungsdatum'], format='%d-%m-%Y')
df['Month']=df['Buchungsdatum'].dt.month
#df['Betrag'] = pd.to_numeric(df['Betrag'].str.replace(',', '.'))
# Set the category order
df['Category'] = pd.Categorical(df['Category'], categories=all_categories, ordered=True)
pivot_table = df.pivot_table(values='Betrag', index='Category', columns='Month', aggfunc='sum', fill_value=0)
pivot_table.columns = pivot_table.columns.astype(str)  # Convert Period to str
pivot_table = pivot_table.reindex(all_categories)  # Reindex to enforce the order
#    for col in pivot_table.select_dtypes(include=['float', 'int']).columns:
#        pivot_table[col] = pivot_table[col].map('{:.2f}'.format)
file8_path=os.path.join(ressources_dir,file8)
pivot_table.to_csv(file8_path)

print('5 - Process visa account')
df1=df[df['Empfaenger']=='ABRECHNUNG KREDITKARTE'][['Buchungsdatum','Betrag']]
df1['Betrag']=-df1['Betrag']
df2=df[df['Konto']=='{visa_account}'][['Buchungsdatum','Betrag']]
combined_df = pd.concat([df1, df2])
result_df = combined_df.groupby('Buchungsdatum', as_index=False)['Betrag'].sum().sort_values(by='Buchungsdatum', ascending=True)
initial_saldo=0 # to modfiy in config file

result_df['Saldo'] = initial_saldo + result_df['Betrag'].cumsum()


print(result_df)