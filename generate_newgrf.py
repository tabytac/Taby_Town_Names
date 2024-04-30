import math
import os
import shutil
import subprocess
from datetime import datetime
from to_precision import to_precision

# Constants
# DATA_INPUT = ["FR.53.22", "GB.ENG.GLA", "GB.ENG", "GB"]
DATA_INPUT = ["GB", "FR", "DE", "ES", "IT", "NL", "SE", "CH", "RU" ,"US", "CA", "AU", "BR", "CN", "IN", "JP", "MX", "KR", "NZ", "PH", "GB.ENG", "GB.SCT", "GB.WLS"]

SORT_BY_POPULATION = True
POPULATION_THRESHOLD = 0
MERGED_FILE_OVERIDE = False

# Column Indices
COLUMN_FEATURE_TYPE = "P"
COLUMN_TYPE_SUB_TYPE = []

COLUMN_COUNTRY = 8
COLUMN_REGION = 10
COLUMN_SUBREGION = 11
COLUMN_FEATURE_TYPE_LOC = 6
COLUMN_TYPE_SUB_TYPE_LOC = 7
COLUMN_POPULATION = 14
COLUMN_NAME = 1


USE_OPENTTD_DIR = True
OPENTTD_DIR = r"D:\Documents\OpenTTD\content_download\newgrf\Taby_Town_Names"
MAX_TOWNS = 16320  # Due to OpenTTD limit

# File Paths
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(BASE_PATH, "Data")
DATA_URL = "https://download.geonames.org/export/dump/"
LIST_OF_DATA_FILES = ["countryInfo.txt", "admin1CodesASCII.txt", "admin2Codes.txt", "featureCodes_en.txt", "cities15000.zip", "cities5000.zip", "cities1000.zip", "cities500.zip"]
GITHHUB_COUNTRY_DEMOONYM_URL = "https://raw.githubusercontent.com/mledoze/countries/blob/master/dist/countries.csv"
#TODO: add the github url for the country demonyms file
ID_FILE = os.path.join(BASE_PATH, "file_id.txt")
BOILERPLATE_START = """grf {{
    grfid: "{grf_id}";
    name: string(STR_GRF_NAME);
    desc: string(STR_GRF_DESC);
    url: string(STR_GRF_URL);
    version: {version};
    min_compatible_version: 1;
}}

town_names {{
    styles: string(STR_GAME_OPTIONS_TOWN_NAME);
    {{
"""

# Functions
def compile_and_deploy_grf(output_nml, output_grf, openttd_dir):
    os.chdir(os.path.dirname(output_nml))
    subprocess.run(["nmlc", output_nml])
    print(f"Compiled {output_nml} to {output_grf}")
    subprocess.run(["copy", output_grf, openttd_dir], shell=True)
    print(f"Deployed {output_grf} to {openttd_dir}")

def read_id_assignments():
    id_assignments = {}
    if os.path.exists(ID_FILE):
        with open(ID_FILE, 'r') as file:
            for line in file:
                parts = line.split(',')
                if len(parts) == 3:
                    nml_path = parts[0].strip()
                    grf_id = parts[1].strip()
                    try:
                        version = int(parts[2].strip())
                        id_assignments[nml_path] = (grf_id, version)
                    except ValueError:
                        print(f"Error parsing version number from line: {line.strip()}")
                else:
                    print(f"Invalid line format: {line.strip()}")
    return id_assignments


def write_id_assignments(assignments):
    with open(ID_FILE, 'w') as file:
        for key, (id, version) in assignments.items():
            file.write(f"{key},{id},{version}\n")

def get_grf_id_and_version(output_nml, id_assignments):
    if output_nml not in id_assignments:
        new_id = f"TA{len(id_assignments) + 1:02}"
        version = 1
    else:
        new_id, version = id_assignments[output_nml]
        version += 1
    id_assignments[output_nml] = (new_id, version)
    write_id_assignments(id_assignments)
    return new_id, version

def get_name(code, file_path, column_index):
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            columns = line.split('\t')
            if columns[0] == code:
                return columns[column_index]
    return ""

def get_country_region_subregion_names(country_code, region_code, subregion_code):
    country_name = ""
    region_name = ""
    subregion_name = ""
    if country_code:
        country_name = get_name(country_code, os.path.join(DATA_PATH, "countryInfo.txt"), 4)
    if region_code:
        region_name = get_name(f"{country_code}.{region_code}", os.path.join(DATA_PATH, "admin1CodesASCII.txt"), 1)
    if subregion_code:
        subregion_name = get_name(f"{country_code}.{region_code}.{subregion_code}", os.path.join(DATA_PATH, "admin2Codes.txt"), 1)
    return country_name, region_name, subregion_name

def prepare_output_dir(country_code, region_code, subregion_code):
    os.makedirs(output_dir, exist_ok=True)
    #instead of copying the template directory, make a new directory and create the english.lng file in it
    template_dir = os.path.join(BASE_PATH, "Template")
    try:
        shutil.copytree(template_dir, output_dir, dirs_exist_ok=True)
    except FileExistsError:
        print("Directory already exists, contents will be merged")


def update_language_file(country_code, region_code, subregion_code, version, num_towns, lowest_population):
    lang_file_path = os.path.join(output_dir, 'lang', 'english.lng')
    #if the lang file not exits, make the folder, then english.lng file 
    if not os.path.exists(lang_file_path):
        os.makedirs(os.path.join(output_dir, 'lang'), exist_ok=True)
        with open(lang_file_path, 'w', encoding='utf-8') as file:
            file.write("/* Taby Town Names */\n")
            file.write("STR_GRF_NAME: \"Taby Town Names\"\n")
            file.write("STR_GRF_DESC: \"Adds a large number of town names to OpenTTD.\"\n")
            file.write("STR_GRF_URL: \"\n")
    with open(lang_file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    country_name, region_name, subregion_name = get_country_region_subregion_names(country_code, region_code, subregion_code)
    country_name_a = f"{country_name}".strip()
    if region_name != "":
        country_name_a = f"{country_name} {region_name}".strip()

    if subregion_name != "":
        country_name_a = f"{country_name} {region_name} {subregion_name}".strip()


    # if the coutnry name is empty and the region code is too, then we are processing the world file
    country_name_b = country_name_a
    if country_name_a == "":
        country_name_a = "World"
        country_name_b = "the world"

    current_date = datetime.now().strftime("%Y-%m-%d")

    content = content.replace("[COUNTRY_NAME_A]", country_name_a)
    content = content.replace("[COUNTRY_NAME_B]", country_name_b)
    content = content.replace("[VERSION]", str(version))
    content = content.replace("[DATE]", current_date)
    content = content.replace("[NUM_TOWNS]", str(num_towns))
    content = content.replace("[LOWEST_POPULATION]", lowest_population)

    with open(lang_file_path, 'w', encoding='utf-8') as file:
        file.write(content)

def read_and_process_towns(file_path, country_code, region_code, subregion_code):
    towns = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            columns = line.split('\t')
            if (country_code and columns[COLUMN_COUNTRY] != country_code) or \
               (region_code and columns[COLUMN_REGION] != region_code) or \
                (subregion_code and columns[COLUMN_SUBREGION] != subregion_code) or \
               (columns[COLUMN_FEATURE_TYPE_LOC] != COLUMN_FEATURE_TYPE) or \
                (COLUMN_TYPE_SUB_TYPE and columns[COLUMN_TYPE_SUB_TYPE_LOC] not in COLUMN_TYPE_SUB_TYPE) or \
               (int(columns[COLUMN_POPULATION]) < POPULATION_THRESHOLD):
                continue
            name = columns[COLUMN_NAME].replace("'", "’").strip().replace('"', "'")
            population = int(columns[COLUMN_POPULATION])
            weight = math.floor(math.sqrt(math.sqrt(population)))
            towns.append((name, population, weight))
    return towns

def sort_town_records(town_records, sort_by_population):
    if sort_by_population:
        town_records.sort(key=lambda x: x[1], reverse=True)
    else:
        town_records.sort(key=lambda x: x[0])
    return town_records

def calculate_town_weights(town_records):
    max_weight = max((w for _, _, w in town_records), default=0)
    min_weight = min((w for _, _, w in town_records), default=0)
    scale = 127 / (max_weight - min_weight) if max_weight != min_weight else 0
    return min_weight, scale

def write_nml_file(output_nml, grf_id, version, town_records, min_weight, scale):
    with open(output_nml, 'w+', encoding='utf-8') as f_out:
        f_out.write(BOILERPLATE_START.format(grf_id=grf_id, version=version))
        for name, _, weight in town_records:
            scaled_weight = max(1, min(int((weight - min_weight) * scale), 127))
            full_name = f"\ttext(\"{name}\", {scaled_weight}),\n"
            f_out.write(full_name)
        f_out.write("}\n}\n")

def determine_input_data(country_code):
    # Check if merged file should be used
    if MERGED_FILE_OVERIDE or country_code == "":
        if not os.path.exists(os.path.join(DATA_PATH, "allCountries.txt")):
            download_data_files("allCountries.zip")
        file_path = os.path.join(DATA_PATH, "allCountries.txt")
    else:
        file_path = os.path.join(DATA_PATH, f"Data/{country_code}.txt")
    

    if not os.path.exists(os.path.join(DATA_PATH, "Data")):
        os.makedirs(os.path.join(DATA_PATH, "Data"), exist_ok=True)
    if not os.path.exists(file_path):
        download_and_extract_country_file(country_code, file_path)
    
    return file_path

def download_and_extract_country_file(country_code, file_path):
    zip_file = f"{country_code}.zip"
    zip_path = os.path.join(DATA_PATH, f"Data/{zip_file}")
    print(zip_path)
    
    # URL to download the file
    download_url = DATA_URL + zip_file
    
    # Download the zip file
    print(f"Downloading {download_url}")
    subprocess.run(["curl", "-o", zip_path, download_url], check=True)

    # Extract the zip file
    print(f"Extracting {zip_path}")
    subprocess.run(["tar", "-xf",zip_path, "-C",f"{DATA_PATH}/Data"], check=True)
    
    # Clean up the zip file
    os.remove(zip_path)
    
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Expected data file not found: {file_path}")

def download_data_files(file_name):
    file_path = os.path.join(DATA_PATH, file_name)
    download_url = DATA_URL + file_name
    print(f"Downloading {download_url}")
    subprocess.run(["curl", "-o", file_path, download_url], check=True)
    if file_name.endswith(".zip"):
        zip_path = file_path
        print(f"Extracting {zip_path}")
        subprocess.run(["tar", "-xf", zip_path, "-C", DATA_PATH], check=True)
        file_path = file_path.replace(".zip", ".txt")
        os.remove(zip_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Expected data file not found: {file_path}")

def process_town_data(country_code, region_code, subregion_code):
    print(f"Processing {country_code} {region_code} {subregion_code}")
    try:
        input_data = determine_input_data(country_code)
        print(f"Data file used: {input_data}")
    except Exception as e:
        print(e)
        return  # or handle error appropriately
    town_records = read_and_process_towns(input_data, country_code, region_code, subregion_code)
    town_records = sort_town_records(town_records, SORT_BY_POPULATION)
    town_records = town_records[:MAX_TOWNS]
    min_weight, scale = calculate_town_weights(town_records)
    #round num_towns down to nearest 2500 and format with commas
    num_towns = "{:,}".format(len(town_records) - (len(town_records) % 2500)  )
    # get the lowest population town and round to 3 significant figures for readability. format with commas
    #check if lowest population before formatting is 0
    # print(len(town_records))
    # lowest_population = ""
    if town_records[-1][1] < 100:
        lowest_population = ""
    else:
        lowest_population = "{:,}".format(int(to_precision(town_records[-1][1], 3, 'std')))
        lowest_population = f" that have a population of {lowest_population} and higher"
    return town_records, min_weight, scale, num_towns, lowest_population


def process_country_region(country_code, region_code, subregion_code):
    # Adjust file paths and names based on country and region
    country_file_code = country_code if country_code else "World"
    location_dir = f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names"
    output_dir = os.path.join(BASE_PATH, "Source_Files", location_dir)
    output_nml = os.path.join(output_dir, f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names.nml")
    output_grf = os.path.join(output_dir, f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names.grf")
    prepare_output_dir(country_code, region_code, subregion_code)
    
    town_records, min_weight, scale, num_towns, lowest_population = process_town_data(country_code, region_code, subregion_code)

    # Assuming ID and other operations are similar for each pair
    id_assignments = read_id_assignments()
    grf_id, version = get_grf_id_and_version(output_nml, id_assignments)
    
    update_language_file(country_code, region_code, subregion_code, version, num_towns, lowest_population)

    write_nml_file(output_nml, grf_id, version, town_records, min_weight, scale)
    if USE_OPENTTD_DIR:
        compile_and_deploy_grf(output_nml, output_grf, OPENTTD_DIR)
    else:
        if not os.path.exists(BASE_PATH + "/Output"):
            os.makedirs(BASE_PATH + "/Output", exist_ok=True)
        compile_and_deploy_grf(output_nml, output_grf, BASE_PATH + "\Output")
    print(f"Processed {len(town_records)} towns for {country_code} {region_code} {subregion_code}")

def take_input():
    data_input = []
    while True:
        user_input = input("Enter a country code, region code, and subregion code separated by periods (e.g. GB.ENG.GLA for all names in London) or enter 'done' to finish: ")
        if user_input == "done":
            break
        data_input.append(user_input)
    return data_input


def get_input(data_input):  
    input_list_data = []
    for code in data_input:
        parts = code.split(".")
        if len(parts) == 3:
            country_code, region_code, subregion_code = parts
        elif len(parts) == 2:
            country_code, region_code = parts
            subregion_code = ""
        else:
            country_code = parts[0]
            region_code = ""
            subregion_code = ""
        country_name, region_name, subregion_name = get_country_region_subregion_names(country_code, region_code, subregion_code)
        print (f"{country_name} {region_name} {subregion_name}")
        user_input = input("Do you want to add this code combination to the data input list? (yes = y, no = n, add all = a): ")
        if user_input == "y":
            input_list_data.append(code)
        elif user_input == "a":
            input_list_data.append(code)

    return input_list_data

def split_input(code):
    parts = code.split(".")
    if len(parts) == 3:
        country_code, region_code, subregion_code = parts
    elif len(parts) == 2:
        country_code, region_code = parts
        subregion_code = ""
    else:
        country_code = parts[0]
        region_code = ""
        subregion_code = ""
    return country_code, region_code, subregion_code

def main():
    #check if the data directory exists and if not create it
    #check if the correct files are in the data directory
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH, exist_ok=True)
    for file in LIST_OF_DATA_FILES:
        file_text = file.replace(".zip", ".txt")
        if not os.path.exists(os.path.join(DATA_PATH, file_text)):
            download_data_files(file)
            print(f"Downloaded {file}")
    data_input = take_input()
    print("Data input list:")
    print(data_input)
    for code in data_input:
        print(f"Processing {code}")
        country_code, region_code, subregion_code = split_input(code)
        process_country_region(country_code, region_code, subregion_code)

if __name__ == "__main__":
    main()
