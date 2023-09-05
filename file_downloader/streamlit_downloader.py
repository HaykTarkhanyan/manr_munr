import os
import requests
import streamlit as st

download_folder = st.text_input('Ո՞ր պապկայի մեջ սեյվ անեմ', "files")

if not os.path.exists(download_folder):
    os.makedirs(download_folder)

def download(url, index, folder=download_folder, output=False):
    file_name = f"{index}. {url.split('/')[-1]}".replace('%20', ' ')
    save_path = os.path.join(folder, file_name)
    
    if output:
        st.write(f'Downloading {url} to {save_path}')	
        
    resp = requests.get(url)

    output = open(save_path, 'wb')
    output.write(resp.content)
    output.close()

    if output:
        st.write('Download complete to server.') 
        

URLS = {'https://www.cba.am/IMRM/YC/YC.xlsx' : 1, 
        'https://www.cba.am/stat/stat_data_arm/secondary%20market.xlsx': 3, 
        'https://www.cba.am/stat/stat_data_arm/Internet-Baza_2023%20ARMnew.xlsx': 5, 
        'https://www.cba.am/stat/stat_data_arm/FOREX%20ARM.xls': 8}

st.title("File Downloader")

if st.button('Download All'):
    for u, i in URLS.items():
        download(u, i)

for f in os.listdir(download_folder):
    st.write(f)
    st.download_button(label='Download', data=f, file_name=f)

st.markdown("go [here](https://amx.am/en/market_data/government_bonds) and press Download All, name it `2. Bond ...`")
st.markdown("go [here](https://www.cba.am/AM/SitePages/Default.aspx) and make export webpage to pdf, name it `4 and 7 ...`")
st.markdown("go [here](https://moneymarket.am/index.php?language=Hay&page=menuinfo&id1=1&id2=1&id3=1) and make export webpage to pdf, name it `6 money market ...`")

        