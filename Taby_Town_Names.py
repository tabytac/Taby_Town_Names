import math
import os
import shutil
import subprocess
from datetime import datetime
from to_precision import to_precision

# Constants
COUNTRY_CODE = "GB"
REGION_CODE = "ENG"

SORT_BY_POPULATION = True
POPULATION_THRESHOLD = 0
MERGED_FILE_OVERIDE = False

# Column Indices
COLUMN_FEATURE_TYPE = "P"
COLUMN_TYPE_SUB_TYPE = []

COLUMN_COUNTRY = 8
COLUMN_REGION = 10
COLUMN_FEATURE_TYPE_LOC = 6
COLUMN_TYPE_SUB_TYPE_LOC = 7
COLUMN_POPULATION = 14
COLUMN_NAME = 1

MAX_TOWNS = 16320  # Due to OpenTTD limit

# File Paths
BASE_PATH = r"D:\Files\Code\OpenTTD NewGRF\Taby Town Names"
OPENTTD_DIR = r"D:\Documents\OpenTTD\content_download\newgrf\Taby Town Names"
DATA_PATH = os.path.join(BASE_PATH, "Data")
FILE_COUNTRY_CODE = "World" if COUNTRY_CODE == "" else COUNTRY_CODE
REGIONAL_DIR = f"Taby {FILE_COUNTRY_CODE}{' ' + REGION_CODE if REGION_CODE else ''} Town Names"
OUTPUT_DIR = os.path.join(BASE_PATH, REGIONAL_DIR)
OUTPUT_NML = os.path.join(OUTPUT_DIR, f"Taby {FILE_COUNTRY_CODE}{' ' + REGION_CODE if REGION_CODE else ''} Town Names.nml")
OUTPUT_GRF = os.path.join(OUTPUT_DIR, f"Taby {FILE_COUNTRY_CODE}{' ' + REGION_CODE if REGION_CODE else ''} Town Names.grf")
ID_FILE = os.path.join(BASE_PATH, "file_id.txt")
MERGED_FILE = os.path.join(DATA_PATH, "allCountries.txt")
SINGLE_FILE = os.path.join(DATA_PATH, "Data", f"{FILE_COUNTRY_CODE}.txt")
if COUNTRY_CODE == "":
    input_data = MERGED_FILE
input_data = MERGED_FILE if MERGED_FILE_OVERIDE or COUNTRY_CODE == "" else SINGLE_FILE
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

def read_id_assignments():
    if os.path.exists(ID_FILE):
        with open(ID_FILE, 'r') as file:
            return {line.split(',')[0].strip(): (line.split(',')[1].strip(), int(line.split(',')[2].strip())) for line in file}
    return {}

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

def get_region_name(region_code):
    with open(os.path.join(DATA_PATH, "admin1CodesASCII.txt"), 'r', encoding='utf-8') as f:
        for line in f:
            columns = line.split('\t')
            if columns[0] == COUNTRY_CODE + "." + REGION_CODE:
                return columns[1]
    return ""

def update_language_file(lang_file_path, country_code, region_code, version, num_towns, lowest_population):
    if os.path.exists(lang_file_path):
        with open(lang_file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        country_name = get_country_name(country_code)
        region_name = get_region_name(region_code)
        if region_name == "":
            country_name_a = f"{country_name}".strip()
        else:
            country_name_a = f"{country_name} ({region_name})".strip()
        country_name_b = country_name_a


        # if the coutnry name is empty and the region code is too, then we are processing the world file
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

def read_and_process_towns(file_path):
    towns = []
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            columns = line.split('\t')
            if (COUNTRY_CODE and columns[COLUMN_COUNTRY] != COUNTRY_CODE) or \
               (REGION_CODE and columns[COLUMN_REGION] != REGION_CODE) or \
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

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    template_dir = os.path.join(BASE_PATH, "Template")
    try:
        shutil.copytree(template_dir, OUTPUT_DIR, dirs_exist_ok=True)
    except FileExistsError:
        print("Directory already exists, contents will be merged")

    id_assignments = read_id_assignments()
    grf_id, version = get_grf_id_and_version(OUTPUT_NML, id_assignments)

    town_records = read_and_process_towns(input_data)
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


    update_language_file(os.path.join(OUTPUT_DIR, 'lang', 'english.lng'), COUNTRY_CODE, REGION_CODE, version, num_towns, lowest_population)

    write_nml_file(OUTPUT_NML, grf_id, version, town_records, min_weight, scale)
    compile_and_deploy_grf(OUTPUT_NML, OUTPUT_GRF, OPENTTD_DIR)
    print(f"Processed {len(town_records)} towns")

if __name__ == "__main__":
    main()
