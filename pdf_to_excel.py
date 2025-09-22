from pdf2image import convert_from_path
import re
import pytesseract
import pandas as pd
import datetime
import os
import sys

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)

pdf_path = sys.argv[1]
#output_excel = sys.argv[2]
poppler_path=r"C:\Program Files\poppler-25.07.0\Library\bin" #add the poppler path here, r = raw string, to ignore escape sequences
pages = convert_from_path(pdf_path, poppler_path=poppler_path, dpi=300) #convert pdf to image format


def get_acc_and_bank(pages):
    
    acc_num=''
    combined_df=pd.DataFrame()
    for page in pages:
        df = pytesseract.image_to_data(page, output_type=pytesseract.Output.DATAFRAME,config='--psm 3') #convert each page(image) to dataframe, psm = page segmentation mode
        df = df[df['text'].notna() & (df['text'].str.strip() != '')] # dropna and '' rows
        combined_df=pd.concat([combined_df,df],ignore_index=True)
        
    temp_list=combined_df['text']
    #print(temp_list)
    for index,item in enumerate(temp_list):
        if item=='Account' and (temp_list[index+1]=='Number' or  temp_list[index+2]=='Number'):
            acc_num=temp_list[index+4]
            break
    
    bank_name=''
    known_banks = ["SBI","HDFC","ICICI","Union","Canara","Axis"]
    
    text=''
    text_list=[]
    
    text=pytesseract.image_to_string(pages[0])     
    text_list=text.split() 
    for item in text_list:
        if item in known_banks:
            bank_name=item
            break
            
    bank_name+=" Bank"   
    
    return acc_num,bank_name 

def extract_particulars(page): #extract particulars column seperately

    crop_box=(400,100,950,3200) #(left,top,right,bottom)
    cropped = page.crop(crop_box)
    #cropped.show()

    df = pytesseract.image_to_data(cropped, output_type=pytesseract.Output.DATAFRAME,config='--psm 12') #convert each page(image) to dataframe, psm = page segmentation mode
    df=df.dropna()
    #print(df['text'])

    grouped=df.groupby(['block_num','line_num','page_num','par_num'])
    block_list=[]

    for _, group in grouped:
        text = ' '.join(group.sort_values('left')['text'])
        top = group['top'].min()
        block_list.append((text, top)) #convert into list of tuples


    text,top=zip(*block_list) #transpose and unpack
    text_list=list(text)
    top_list=list(top)

    particulars=[]

    i = 0
    while i < len(text_list):
        if i + 1 < len(text_list):
            gap = top_list[i + 1] - top_list[i]

            if gap < 52: #found by comparing spaces between lines, numerical value given by tesseract
                grouped = text_list[i] + " " + text_list[i + 1]
                particulars.append(grouped) #append the dual lines in a cell as one element
                i += 2  #Skip two so that we don't group (1,2) and then (2,3) etc. If (1,2) is grouped, then group (3,4).
            else:
                particulars.append(text_list[i]) #append the single line in a cell seperately
                i += 1
        else:
            particulars.append(text_list[i]) #Last single line without a pair
            i += 1
            
    #for i in particulars:
        #print(i)  
    #print(len(particulars))   
    return particulars
    
temp=[]
for page in pages:
    temp.extend(extract_particulars(page))
    pass

#print("temp",temp)    
    
final_particulars = []
flag=0
for  item in temp:
    if item=='Particulars':
        flag=1
        continue
    if item=='Summary : |':
        flag=0
    if flag==1 and item!='Torte':
        final_particulars.append(item)
        
final_particulars=final_particulars[1:] #to remove 'Opening Balance' at index 0
    
def all_pages_to_text(pages): #to convert image->string and only keep the [data in tables] as text 
    
    text=''
    text_list=[]
    
    for page in pages:
        text=text+pytesseract.image_to_string(page)
        
    text_list=text.splitlines()
    #print(text_list)
    
    final_list=[]
    flag=0
    for item in text_list:
        if 'Opening Balance' in item:
            flag=1
        if 'Total Debits' in item:
            flag=0
        if flag==1:
            final_list.append(item)
    return final_list
   

def extract_rest(pages): #extract all other details
    
    combined_df=pd.DataFrame()
    for page in pages:
        df = pytesseract.image_to_data(page, output_type=pytesseract.Output.DATAFRAME,config='--psm 3') #convert each page(image) to dataframe, psm = page segmentation mode
        df = df[df['text'].notna() & (df['text'].str.strip() != '')] # dropna and '' rows
        combined_df=pd.concat([combined_df,df],ignore_index=True)
    #print(combined_df[['top','left','text']]) 
    rows = []
    start_collecting = False
    for _, row in combined_df.iterrows():
        if row['text'] == 'Balance':
            start_collecting = True
        if start_collecting:
            rows.append(row)
        if row['text'] == 'Summary' and start_collecting: #extract info from the tables to the df
            break

    extracted_df = pd.DataFrame(rows)

    #print(extracted_df[['top','left','text']])
    
    temp_chqnum=[]
    temp_withdrawal=[]
    temp_deposit=[]
    temp_balance=[]
    
    for _, row in extracted_df.iterrows():  # starting of 'left': cheque_num = 967, withdrawal = 1265 , deposit = 1593, balance = 1899
        left = row['left']
    
        if 967 <= left < 1265:
            temp_chqnum.append(row['text'])
        elif 1265 <= left < 1593:
            temp_withdrawal.append(row['text'])
        elif 1593 <= left < 1899:
            temp_deposit.append(row['text'])
        elif left >= 1899:
            temp_balance.append(row['text'])
            
    chqnum=[]        
    for i in temp_chqnum:
        if i.isdigit():
            chqnum.append(i)
            
    withdrawal= []
    for i in temp_withdrawal:
        if all(char in "0123456789,." for char in i):
            withdrawal.append(i)
            
    deposit=[]
    for i in temp_deposit:
        if all(char in "0123456789,." for char in i):
            deposit.append(i)
            
    balance=[]
    for i in temp_balance:
        if all(char in "0123456789,." for char in i) and len(i)>=2:
            balance.append(i)
            
    #print("chqnum:",chqnum,"\n\nwithdrawal:",withdrawal,"\n\ndeposit:",deposit,"\n\nbalance:",balance)
    
    all_data_in_text=all_pages_to_text(pages)
    date_pattern = r'\b\d{2}-\d{2}-\d{4}\b'
    serial_num_pattern = r'^\s*\d+\s+\|'
    
    #for i in all_data_in_text:
        #print(i)
    all_data_in_text = [item for item in all_data_in_text 
                        if re.search(date_pattern, str(item)) or re.search(serial_num_pattern, str(item))] #to get only the table data
    #print("\n\n",len(all_data_in_text))
    #for i in all_data_in_text:
        #print(i)
    
    final_chqnum=[]
    final_withdrawal=[]
    final_deposit=[]
    final_balance=[]
    final_date=[]
    
    for item in all_data_in_text:
        #chqnum
        for num in chqnum:
            if num in item.split():
                final_chqnum.append(num)
                break
        else:
            final_chqnum.append(' ')
                
        #withdrawal        
        for num in withdrawal:
            if num in item.split():
                final_withdrawal.append(num)
                break
        else:
            final_withdrawal.append(' ')
                
        #deposit            
        for num in deposit:
            if num in item.split():
                final_deposit.append(num)
                break
        else:
            final_deposit.append(' ')
    #balance                
    final_balance = balance[1:] #to remove opening balance amount at index 0
    
    #date
    for line in all_data_in_text:
        match = re.search(date_pattern, line)
        if match:
            final_date.append(match.group())
        else:
            final_date.append('') 
    
    #print("chqnum:",len(final_chqnum),"\n\nwithdrawal:",len(final_withdrawal),"\n\ndeposit:",len(final_deposit),"\n\nbalance:",len(final_balance),"\n\ndate:",len(final_date))
    return final_date, final_chqnum, final_withdrawal, final_deposit, final_balance
    
def convert_final_to_excel(acc_num,bank_name,final_date,final_particulars,final_chqnum, final_withdrawal, final_deposit, final_balance):
    
    final_acc=[]
    final_bank=[]
    for i in range(len(final_balance)):
        final_acc.append(acc_num)
        final_bank.append(bank_name)
        
    final_df=pd.DataFrame({
        'Bank Account No': final_acc,
        'Bank Name': final_bank,
        'Date': final_date,
        'Particulars': final_particulars,
        'Chq Num': final_chqnum,
        'Withdrawal': final_withdrawal,
        'Deposit': final_deposit,
        'Balance': final_balance 
    })
    
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    filename = rf"C:/xampp/htdocs/pdf_to_excel/outputs/bank_statement_{timestamp}.xlsx"
    final_df.to_excel(filename, index=False)
    #print("Success")
    return filename
#print("\n\nparticulars:",len(final_particulars))


final_date, final_chqnum, final_withdrawal, final_deposit, final_balance=extract_rest(pages)
acc_num,bank_name=get_acc_and_bank(pages)

output_file=convert_final_to_excel(acc_num,bank_name,final_date,final_particulars,final_chqnum, final_withdrawal, final_deposit, final_balance)
sys.stdout.write(output_file)
#print("\naccount:",acc_num,"\nbank:",bank_name)


