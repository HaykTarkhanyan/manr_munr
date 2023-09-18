import pandas as pd
import json

homework_num = "Համար"
subproblem_num = ""
answer = "Պատասխան"
correct = "Ճի՞շտ է"

writer = pd.ExcelWriter('homework_tracker.xlsx', engine='xlsxwriter')



with open('shtemaran_structure.json', 'r', encoding='utf-8') as f:
    shtemaran_structure = json.load(f)

first = shtemaran_structure['Առաջին']

def create_sheet(topic_name, num_homeworks, num_subproblems, category_name):
    df = pd.DataFrame(columns=[num_homeworks])
    for i in range(1, num_homeworks+1):
        df.loc[i-1, num_homeworks] = i
        for j in range(1, num_subproblems+1):
            df[subproblem_num + str(j)] = ''
        df[correct] = False
    df.to_excel(writer, sheet_name=category_name + topic_name, index=False)

def create_homework_tracker(homework_dict):
    
    for category_name, category in homework_dict.items():
        if category_name == 'Պնդումների փունջ':
            num_subproblems = 6
        else:
            num_subproblems = 4

        for topic_name, num_exercises in category.items():            
            create_sheet(topic_name, num_exercises, num_subproblems, category_name)
        
    writer.save()

create_homework_tracker(first)
