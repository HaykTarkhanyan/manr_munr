import os
from tqdm import tqdm

# The directory that we are interested in
myPath = "../../../"

# The min size of the file in Bytes
mySize = 300_000_000

# All the file paths will be stored in this list
filesList= []
folders_to_ignore = ["YSU OpenCourseWare", "videos Python"]

files_dict = {}

for path, subdirs, files in tqdm(os.walk(myPath)):
    for name in files:
        filesList.append(os.path.join(path, name))

for i in filesList:
    if any(folder in i for folder in folders_to_ignore):
        continue
    # Getting the size in a variable
    try:
        fileSize = os.path.getsize(str(i))

        # Print the files that meet the condition
        if int(fileSize) >= mySize:
            files_dict[i] = fileSize // 2024 // 1024
    except:
        pass
    
# sort the dictionary by size
sorted_files = dict(sorted(files_dict.items(), key=lambda item: item[1], reverse=True))

dict_new = {}
# print the files
for file, size in sorted_files.items():
    if size > 1000:
        print(f"{size/1024:.2f} gb - {file} ")
    else:
        print(f"{size} mb - {file} ")
        
# save to json  
import json
with open('file_sizes.json', 'w') as f:
    json.dump(sorted_files, f)