import math
import os
import shutil
import subprocess
from datetime import datetime
from to_precision import to_precision

# Constants
# COUNTRY_REGION_PAIRS = [["GB", ""], ["GB", "ENG"], ["GB", "SCT"], ["GB", "WLS"], ["FR", ""], ["DE", ""], ["IT", ""], ["US", ""], ["CA", ""], ["JP", ""], ["RU", ""], ["CN", ""], ["IN", ""], ["AU", ""], ["NZ", ""], ["BR", ""], ["PH", ""], ["ES", ""], ["", ""]]
# COUNTRY_REGION_TRIPLES = [["GB", "", ""], ["GB", "ENG", ""], ["GB", "SCT", ""], ["GB", "WLS", ""], ["FR", "", ""], ["DE", "", ""], ["IT", "", ""], ["US", "", ""], ["CA", "", ""], ["JP", "", ""], ["RU", "", ""], ["CN", "", ""], ["IN", "", ""], ["AU", "", ""], ["NZ", "", ""], ["BR", "", ""], ["PH", "", ""], ["ES", "", ""], ["", "", ""]]
COUNTRY_REGION_TRIPLES = [["VA", "", ""]]

SORT_BY_POPULATION = False
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

OPENTTD_DIR = r"D:\Documents\OpenTTD\content_download\newgrf\Taby_Town_Names"
MAX_TOWNS = 16320  # Due to OpenTTD limit

# File Paths
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(BASE_PATH, "Data")
DATA_URL = "https://download.geonames.org/export/dump/"
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

def get_country_name(country_code):
    with open(os.path.join(DATA_PATH, "countryInfo.txt"), 'r', encoding='utf-8') as f:
        for line in f:
            columns = line.split('\t')
            if columns[0] == country_code:
                return columns[4]
    return ""

def get_region_name(country_code, region_code):
    with open(os.path.join(DATA_PATH, "admin1CodesASCII.txt"), 'r', encoding='utf-8') as f:
        for line in f:
            columns = line.split('\t')
            if columns[0] == f"{country_code}.{region_code}":
                return columns[1]
    return ""
def get_subregion_name(country_code, region_code, subregion_code):
    with open(os.path.join(DATA_PATH, "admin2Codes.txt"), 'r', encoding='utf-8') as f:
        for line in f:
            columns = line.split('\t')
            if columns[0] == f"{country_code}.{region_code}.{subregion_code}":
                return columns[1]
    return ""

def update_language_file(lang_file_path, country_code, region_code, subregion_code, version, num_towns, lowest_population):
    if os.path.exists(lang_file_path):
        with open(lang_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        country_name = get_country_name(country_code)
        region_name = get_region_name(country_code, region_code)
        subregion_name = get_subregion_name(country_code, region_code, subregion_code)
        # if region_name == "":
        #     country_name_a = f"{country_name}".strip()
        # else:
        #     country_name_a = f"{country_name} ({region_name})".strip()
        # country_name_b = country_name_a
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
    else:
        print(f"Language file not found: {lang_file_path}")

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
    if MERGED_FILE_OVERIDE or country_code == "":
        try:
            function_return = os.path.join(DATA_PATH, "allCountries.txt")
            return function_return
        except FileNotFoundError:
            print("Merged file not found")
    try:
        function_return = os.path.join(DATA_PATH, "Data", f"{country_code}.txt")
        return function_return
    except FileNotFoundError:
        print("File not found, downloading")
        os.chdir(os.path.dirname(os.path.join(DATA_PATH, "Data")))
        subprocess.run(["curl", DATA_URL + f"{country_code}.zip", "--output", f"{DATA_PATH}/Data/{country_code}.zip"])
        print(DATA_URL + f"Data/{country_code}.zip")
        subprocess.run(["tar", "-xf", f"{DATA_PATH}\\Data\\{country_code}.zip", "-C", f"{DATA_PATH}\\Data"])
        print (f"{DATA_PATH}/Data/{country_code}.zip")
        os.remove(f"{DATA_PATH}/Data/{country_code}.zip")
        os.remove(f"{DATA_PATH}/Data/readme.txt")
        function_return = os.path.join(DATA_PATH, "Data", f"{country_code}.txt")
        return function_return



def process_town_data(country_code, region_code, subregion_code):
    print(f"Processing {country_code} {region_code} {subregion_code}")
    input_data = determine_input_data(country_code)
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
    output_dir = os.path.join(BASE_PATH, location_dir)
    output_nml = os.path.join(output_dir, f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names.nml")
    output_grf = os.path.join(output_dir, f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names.grf")
    os.makedirs(output_dir, exist_ok=True)
    template_dir = os.path.join(BASE_PATH, "Template")
    try:
        shutil.copytree(template_dir, output_dir, dirs_exist_ok=True)
    except FileExistsError:
        print("Directory already exists, contents will be merged")

    town_records, min_weight, scale, num_towns, lowest_population = process_town_data(country_code, region_code, subregion_code)

    # Assuming ID and other operations are similar for each pair
    id_assignments = read_id_assignments()
    grf_id, version = get_grf_id_and_version(output_nml, id_assignments)
    
    update_language_file(os.path.join(output_dir, 'lang', 'english.lng'), country_code, region_code, subregion_code, version, num_towns, lowest_population)

    write_nml_file(output_nml, grf_id, version, town_records, min_weight, scale)
    compile_and_deploy_grf(output_nml, output_grf, OPENTTD_DIR)
    print(f"Processed {len(town_records)} towns for {country_code} {region_code} {subregion_code}")

def main():
    for country_region in COUNTRY_REGION_TRIPLES:
        country_code, region_code, subregion_code = country_region
        process_country_region(country_code, region_code, subregion_code)

if __name__ == "__main__":
    main()
