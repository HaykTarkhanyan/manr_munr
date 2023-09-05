import os
import requests

def download(url, index, folder='temp'):
    file_name = f"{index}. {url.split('/')[-1]}".replace('%20', ' ')
    save_path = os.path.join(folder, file_name)
    
    print(f'Downloading {url} to {save_path}')	
    
    resp = requests.get(url)

    output = open(save_path, 'wb')
    output.write(resp.content)
    output.close()
    print('Download complete.') 
    

URLS = {'https://www.cba.am/IMRM/YC/YC.xlsx' : 1, 
        'https://www.cba.am/stat/stat_data_arm/secondary%20market.xlsx': 3, 
        'https://www.cba.am/stat/stat_data_arm/Internet-Baza_2023%20ARMnew.xlsx': 5, 
        'https://www.cba.am/stat/stat_data_arm/FOREX%20ARM.xls': 8}


for u, i in URLS.items():
    download(u, i)



# # screenshots 
# from selenium import webdriver
# from time import sleep

# driver = webdriver.Firefox()
# driver.get('https://www.python.org')
# sleep(1)

# driver.get_screenshot_as_file("screenshot.png")
# driver.quit()
# print("end...")
