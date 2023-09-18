import os
import requests
import argparse

parser = argparse.ArgumentParser(description='Download files to a specified folder')
parser.add_argument('folder', type=str, help='the folder to download files to')
args = parser.parse_args()

download_folder = args.folder



if not os.path.exists(download_folder):
    os.makedirs(download_folder)

def download(url, index, folder=download_folder, output=False):
    file_name = f"{index}. {url.split('/')[-1]}".replace('%20', ' ')
    save_path = os.path.join(folder, file_name)
    
    if output:
        print(f'Downloading {url} to {save_path}')	
        
    resp = requests.get(url)

    output = open(save_path, 'wb')
    output.write(resp.content)
    output.close()

    if output:
        print('Download complete to server.') 
        

URLS = {'https://www.cba.am/IMRM/YC/YC.xlsx' : 1, 
        'https://www.cba.am/stat/stat_data_arm/secondary%20market.xlsx': 3, 
        'https://www.cba.am/stat/stat_data_arm/Internet-Baza_2023%20ARMnew.xlsx': 5, 
        'https://www.cba.am/stat/stat_data_arm/FOREX%20ARM.xls': 8}


for u, i in URLS.items():
    download(u, i)

print("go [here](https://amx.am/en/market_data/government_bonds) and press Download All, name it `2. Bond ...`")
print("go [here](https://www.cba.am/AM/SitePages/Default.aspx) and make export webpage to pdf, name it `4 and 7 ...`")
print("go [here](https://moneymarket.am/index.php?language=Hay&page=menuinfo&id1=1&id2=1&id3=1) and make export webpage to pdf, name it `6 money market ...`")

# st.markdown("go [here](https://amx.am/en/market_data/government_bonds) and press Download All, name it `2. Bond ...`")
# st.markdown("go [here](https://www.cba.am/AM/SitePages/Default.aspx) and make export webpage to pdf, name it `4 and 7 ...`")
# st.markdown("go [here](https://moneymarket.am/index.php?language=Hay&page=menuinfo&id1=1&id2=1&id3=1) and make export webpage to pdf, name it `6 money market ...`")

        