from itertools import combinations, chain
from scipy.optimize import minimize
import json
import time

# 加載 JSON 數據
def load_prescription_database(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        database = json.load(file)
    return database

prescription_database = load_prescription_database('prescription_database.json')
print(f"方劑數量:{len(prescription_database.keys())}")

def all_combinations(database, exclude):
    keys = [key for key in database.keys() if key != exclude]
    return chain(*[combinations(keys, i) for i in range(1, min(len(keys), 2)+1)])

def calculate_herbs_dosage(dosages, combination, database):
    herbs_dosage = {}
    for dosage, prescription in zip(dosages, combination):
        for herb, amount in database[prescription].items():
            if herb in herbs_dosage:
                herbs_dosage[herb] += amount * dosage
            else:
                herbs_dosage[herb] = amount * dosage
    return herbs_dosage

def objective_func(x, target_composition, combination, database, penalty_factor):
    combined_composition = {}
    for i, prescription in enumerate(combination):
        for herb, amount in database[prescription].items():
            if herb in combined_composition:
                combined_composition[herb] += amount * x[i]
            else:
                combined_composition[herb] = amount * x[i]

    difference = 0
    for herb, target_amount in target_composition.items():
        combined_amount = combined_composition.get(herb, 0)
        difference += (target_amount - combined_amount) ** 2

    non_target_herbs_count = len(set(combined_composition.keys()) - set(target_composition.keys()))
    difference += penalty_factor * non_target_herbs_count

    return difference

def calculate_match_with_highlights(target_composition, combination, database, penalty_factor):
    initial_guess = [1 for _ in combination]
    bounds = [(0, 200) for _ in combination]
    result = minimize(objective_func, initial_guess, args=(target_composition, combination, database, penalty_factor), method='SLSQP', bounds=bounds)

    if result.success:
        dosages = result.x
        herbs_dosage = calculate_herbs_dosage(dosages, combination, database)
        combined_composition = calculate_herbs_dosage(dosages, combination, database)
        match_percentage = 100 - objective_func(dosages, target_composition, combination, database, penalty_factor)

        sorted_herbs_dosage = dict(sorted(herbs_dosage.items(), key=lambda item: (item[0] not in target_composition, item[0])))
        highlighted_herbs_dosage = {f"**{herb}**" if herb in target_composition else herb: dosage for herb, dosage in sorted_herbs_dosage.items()}

        remaining_herbs = {herb: target_composition.get(herb, 0) - combined_composition.get(herb, 0) for herb in target_composition}
        remaining_herbs = {herb: amount for herb, amount in remaining_herbs.items() if amount > 0}

        return match_percentage, combination, dosages, highlighted_herbs_dosage, remaining_herbs
    else:
        return 0, combination, [], {}, {}

def adjust_target_composition_for_dosage(target_composition, input_dosage):
    adjusted_target_composition = {}
    for herb, proportion in target_composition.items():
        adjusted_target_composition[herb] = proportion * input_dosage
    return adjusted_target_composition

def parse_prescription_and_dosage(input_str):
    for i in range(len(input_str)-1, -1, -1):
        if not input_str[i].isdigit() and input_str[i] != '.':
            return input_str[:i+1].strip(), float(input_str[i+1:])
    return None, None

def find_best_matches(name, database, adjusted_target_composition, penalty_factor, top_n=5):
    if name and name not in database:
        print("方劑不存在於資料庫中")
        return

    all_possible_combinations = all_combinations(database, name if name else "")
    start = time.time()
    matches = [calculate_match_with_highlights(adjusted_target_composition, combo, database, penalty_factor) for combo in all_possible_combinations]
    print(f"計算匹配度用時: {time.time() - start}")
    best_matches = sorted(matches, key=lambda x: -x[0])[:top_n]

    for match in best_matches:
        match_percentage, combination, dosages, herbs_dosage, remaining_herbs = match
        combination_str = ', '.join([f"{prescription}{dosage:.1f}" for prescription, dosage in zip(combination, dosages)])
        print(f"匹配度: {match_percentage:.2f}%，組合: {combination_str}")
        for herb, dosage in herbs_dosage.items():
            print(f"    {herb}: {dosage:.2f}")
        
        # 收集組合中已出現的藥材
        combined_herbs = set()
        for prescription in combination:
            combined_herbs.update(database[prescription].keys())

        if remaining_herbs:
            print("尚缺藥物：")
            for herb in remaining_herbs.keys():
                if remaining_herbs[herb] > 0 and herb not in combined_herbs:
                    print(f"    {herb}")
        else:
            print("所有目標藥材已被完全匹配。")
        print("\n")



penalty_factor_input = input("請輸入懲罰因子（預設為2）：")
try:
    penalty_factor = float(penalty_factor_input) if penalty_factor_input else 2
except ValueError:
    print("懲罰因子輸入非法，將使用預設值2")
    penalty_factor = 2

user_input = input("請輸入方劑名稱和劑量或藥材組合(例如：補中益氣湯3.5或人參3.0+茯苓2.5)：")

if '+' in user_input:
    herbs_input = user_input.split('+')
    adjusted_target_composition = {}
    unknown_herbs = []
    for herb_input in herbs_input:
        herb, dosage = parse_prescription_and_dosage(herb_input)
        if not any(herb in herbs for prescription in prescription_database.values() for herbs in prescription):
            unknown_herbs.append(herb)
        else:
            if herb in adjusted_target_composition:
                adjusted_target_composition[herb] += dosage
            else:
                adjusted_target_composition[herb] = dosage
    if unknown_herbs:
        print(f"資料庫尚未收錄以下藥物：{', '.join(unknown_herbs)}")
    else:
        find_best_matches(None, prescription_database, adjusted_target_composition, penalty_factor)
else:
    prescription_name, input_dosage = parse_prescription_and_dosage(user_input)
    if prescription_name in prescription_database:
        target_composition = prescription_database[prescription_name]
        adjusted_target_composition = adjust_target_composition_for_dosage(target_composition, input_dosage)
        find_best_matches(prescription_name, prescription_database, adjusted_target_composition, penalty_factor)
    else:
        print("資料庫尚未收錄此方劑。")
