import math
import os
import csv
import subprocess
from datetime import datetime
import ctypes.wintypes

# Constants to modify
DATA_INPUT = [
    "GB",
    "FR",
    "DE",
    "ES",
    "IT",
    "NL",
    "SE",
    "CH",
    "RU",
    "US",
    "CA",
    "AU",
    "BR",
    "CN",
    "IN",
    "JP",
    "MX",
    "KR",
    "NZ",
    "PH",
    "GB.ENG",
    "GB.SCT",
    "GB.WLS",
    "",
]

SORT_BY_POPULATION = True
POPULATION_THRESHOLD = 0
MERGED_FILE_OVERRIDE = False
USE_OPENTTD_DIR = True
MAX_TOWNS = 16320  # Due to OpenTTD limit

# Constants to not modify
COLUMN_FEATURE_TYPE = "P"
COLUMN_TYPE_SUB_TYPE = []
COLUMN_COUNTRY = 8
COLUMN_REGION = 10
COLUMN_SUBREGION = 11
COLUMN_FEATURE_TYPE_LOC = 6
COLUMN_TYPE_SUB_TYPE_LOC = 7
COLUMN_POPULATION = 14
COLUMN_NAME = 1
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
DATA_PATH = os.path.join(BASE_PATH, "Data")
DATA_URL = "https://download.geonames.org/export/dump/"
LIST_OF_DATA_FILES = [
    "countryInfo.txt",
    "admin1CodesASCII.txt",
    "admin2Codes.txt",
    "featureCodes_en.txt",
    "cities15000.zip",
    "cities5000.zip",
    "cities1000.zip",
    "cities500.zip",
]
GITHUB_COUNTRY_DEMONYM_URL = (
    "https://raw.githubusercontent.com/mledoze/countries/master/dist/countries.csv"
)
DEMONYM_COUNTRY_CODE_COLUMN = 3
DEMONYM_COUNTRY_DEMONYM_COLUMN = 64
NEWGRF_LICENSE_URL = "https://www.gnu.org/licenses/old-licenses/gpl-2.0.txt"
ID_FILE = os.path.join(BASE_PATH, "file_id.txt")

NML_BOILERPLATE = """grf {{
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
LANG_FILE_BOILERPLATE = """##grflangid 0x00
STR_GRF_NAME                    :Taby [COUNTRY_NAME_A] Town Names {SILVER}v1.[VERSION]
STR_GRF_DESC                    :{ORANGE}Taby [COUNTRY_NAME_A] Town Names {BLUE}v1.[VERSION]{}{}{WHITE}This NewGRF adds names for towns and cities[LOWEST_POPULATION] in [COUNTRY_NAME_B]. This set has over [NUM_TOWNS] towns with their spawn chance roughly based on the population of the town.{}{}The database of town names and other place names was taken from {LTBLUE}www.geonames.org.{}{}{BLACK}Made by: {GREEN}Tabytac{}{BLACK}Updated: {GREEN}[DATE]{}{}{SILVER}This grf is released under GNU GPL v3 or higher.
STR_GRF_URL                     :https://github.com/Tabytac/Taby-Town-Names
STR_GAME_OPTIONS_TOWN_NAME      :Taby [COUNTRY_NAME_A] Town Names
"""

# Functions


def get_openttd_dir():
    buffer = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
    ctypes.windll.shell32.SHGetFolderPathW(None, 5, None, 0, buffer)
    return os.path.join(buffer.value, "OpenTTD", "content_download", "newgrf",
                        "Taby_Town_Names")


OPENTTD_DIR = (get_openttd_dir() if input(
    "Do you want to use the default OpenTTD directory? (yes = y, no = n): ")
               == "y" else
               input("Enter the directory where the GRF should be copied: "))


def get_name(code, file_path, column_index):
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            columns = line.split("\t")
            if columns[0] == code:
                return columns[column_index]


def get_country_region_subregion_names(country_code, region_code,
                                       subregion_code):
    country_name = ""
    region_name = ""
    subregion_name = ""
    if country_code:
        country_name = get_name(country_code,
                                os.path.join(DATA_PATH, "countryInfo.txt"), 4)
    if region_code:
        region_name = get_name(
            f"{country_code}.{region_code}",
            os.path.join(DATA_PATH, "admin1CodesASCII.txt"),
            1,
        )
    if subregion_code:
        subregion_name = get_name(
            f"{country_code}.{region_code}.{subregion_code}",
            os.path.join(DATA_PATH, "admin2Codes.txt"),
            1,
        )
    return country_name, region_name, subregion_name


def get_country_demonym(country_code):
    if not os.path.exists(os.path.join(DATA_PATH, "countries.csv")):
        download_data_files("countries.csv", GITHUB_COUNTRY_DEMONYM_URL)
    with open(os.path.join(DATA_PATH, "countries.csv"), "r",
              encoding="utf-8") as f:
        reader = csv.reader(f)
        for columns in reader:
            if country_code == columns[DEMONYM_COUNTRY_CODE_COLUMN].strip(
                    '"').strip("'"):
                return columns[DEMONYM_COUNTRY_DEMONYM_COLUMN].strip(
                    '"').strip("'")


def prepare_output_dir(output_dir, country_code, region_code, subregion_code):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    if not os.path.exists(os.path.join(output_dir, "lang")):
        os.makedirs(os.path.join(output_dir, "lang"), exist_ok=True)
    if not os.path.exists(os.path.join(output_dir, "lang", "english.lng")):
        with open(os.path.join(output_dir, "lang", "english.lng"),
                  "w",
                  encoding="utf-8") as file:
            file.write(LANG_FILE_BOILERPLATE)
    if not os.path.exists(
            os.path.join(BASE_PATH, "Source_Files", "license.txt")):
        print("Downloading license file")
        subprocess.run(
            [
                "curl",
                "-o",
                os.path.join(BASE_PATH, "Source_Files", "license.txt"),
                NEWGRF_LICENSE_URL,
            ],
            check=True,
        )
    if not os.path.exists(os.path.join(output_dir, "license.txt")):
        print("Copying license file")
        subprocess.run(
            [
                "copy",
                os.path.join(BASE_PATH, "Source_Files", "license.txt"),
                os.path.join(output_dir, "license.txt"),
            ],
            shell=True,
            check=True,
        )


def to_precision(num, sig_figs):
    if num != 0:
        scale = sig_figs - int(math.floor(math.log10(abs(num)))) - 1
        return round(num, scale)
    return 0


def update_language_file(
    output_dir,
    country_code,
    region_code,
    subregion_code,
    version,
    num_towns,
    lowest_population,
):
    lang_file_path = os.path.join(output_dir, "lang", "english.lng")
    # if the lang file not exits, make the folder, then english.lng file
    if not os.path.exists(lang_file_path):
        os.makedirs(os.path.join(output_dir, "lang"), exist_ok=True)
        with open(lang_file_path, "w", encoding="utf-8") as file:
            file.write("/* Taby Town Names */\n")
            file.write('STR_GRF_NAME: "Taby Town Names"\n')
            file.write(
                'STR_GRF_DESC: "Adds a large number of town names to OpenTTD."\n'
            )
            file.write('STR_GRF_URL: "\n')
    with open(lang_file_path, "r", encoding="utf-8") as file:
        content = file.read()
    country_name, region_name, subregion_name = get_country_region_subregion_names(
        country_code, region_code, subregion_code)
    country_demonym = get_country_demonym(country_code)
    country_demonym_a = f"{country_demonym}".strip()
    if region_name != "":
        country_demonym_a = f"{country_demonym_a} {region_name}".strip()
    if subregion_name != "":
        country_demonym_a = (
            f"{country_demonym_a} {region_name} {subregion_name}".strip())
    country_demonym_b = f"{country_name} {region_name} {subregion_name}".strip(
    )
    if country_demonym_a == "None":
        country_demonym_a = "World"
        country_demonym_b = "the World"

    current_date = datetime.now().strftime("%Y-%m-%d")

    content = content.replace("[COUNTRY_NAME_A]", country_demonym_a)
    content = content.replace("[COUNTRY_NAME_B]", country_demonym_b)
    content = content.replace("[VERSION]", str(version))
    content = content.replace("[DATE]", current_date)
    content = content.replace("[NUM_TOWNS]", str(num_towns))
    content = content.replace("[LOWEST_POPULATION]", lowest_population)
    with open(lang_file_path, "w", encoding="utf-8") as file:
        file.write(content)


def read_and_process_towns(file_path, country_code, region_code,
                           subregion_code):
    towns = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            columns = line.split("\t")
            if ((country_code and columns[COLUMN_COUNTRY] != country_code)
                    or (region_code and columns[COLUMN_REGION] != region_code)
                    or (subregion_code
                        and columns[COLUMN_SUBREGION] != subregion_code) or
                (columns[COLUMN_FEATURE_TYPE_LOC] != COLUMN_FEATURE_TYPE) or
                (COLUMN_TYPE_SUB_TYPE and columns[COLUMN_TYPE_SUB_TYPE_LOC]
                 not in COLUMN_TYPE_SUB_TYPE) or
                (int(columns[COLUMN_POPULATION]) < POPULATION_THRESHOLD)):
                continue
            name = columns[COLUMN_NAME].replace("'",
                                                "’").strip().replace('"', "'")
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


def write_nml_file(output_nml, grf_id, version, town_records, min_weight,
                   scale):
    with open(output_nml, "w+", encoding="utf-8") as f_out:
        f_out.write(NML_BOILERPLATE.format(grf_id=grf_id, version=version))
        for name, _, weight in town_records:
            scaled_weight = max(1, min(int((weight - min_weight) * scale),
                                       127))
            full_name = f'\ttext("{name}", {scaled_weight}),\n'
            f_out.write(full_name)
        f_out.write("}\n}\n")


def determine_input_data(country_code):
    # Check if merged file should be used
    if MERGED_FILE_OVERRIDE or country_code == "":
        if not os.path.exists(os.path.join(DATA_PATH, "allCountries.txt")):
            download_data_files("allCountries.zip",
                                DATA_URL + "allCountries.zip")
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
    subprocess.run(["tar", "-xf", zip_path, "-C", f"{DATA_PATH}/Data"],
                   check=True)

    # Clean up the zip file
    os.remove(zip_path)

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Expected data file not found: {file_path}")


def download_data_files(file_name, download_url):
    file_path = os.path.join(DATA_PATH, file_name)
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
    town_records = read_and_process_towns(input_data, country_code,
                                          region_code, subregion_code)
    town_records = sort_town_records(town_records, SORT_BY_POPULATION)
    town_records = town_records[:MAX_TOWNS]
    min_weight, scale = calculate_town_weights(town_records)
    # round num_towns down to nearest 2500 and format with commas
    num_towns = "{:,}".format(len(town_records) - (len(town_records) % 2500))
    # get the lowest population town and round to 3 significant figures for readability. format with commas
    # check if lowest population before formatting is 0
    # print(len(town_records))
    # lowest_population = ""
    if town_records[-1][1] < 100:
        lowest_population = ""
    else:
        lowest_population = "{:,}".format(
            int(to_precision(town_records[-1][1], 3)))
        lowest_population = f" that have a population of {lowest_population} and higher"
    return town_records, min_weight, scale, num_towns, lowest_population


def compile_and_deploy_grf(output_nml, output_grf, openttd_dir):
    os.chdir(os.path.dirname(output_nml))
    try:
        subprocess.run(["nmlc", output_nml], check=True)
        print(f"Compiled {output_nml}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during compilation: {e}")
    try:
        subprocess.run(["copy", output_grf, openttd_dir],
                       shell=True,
                       check=True)
        print(f"Deployed {output_grf} to {openttd_dir}")
    except subprocess.CalledProcessError as e:
        print(f"Error occurred during deployment: {e}")


def manage_id_assignments(output_nml):
    id_assignments = {}
    id_used = set()
    id_gap = None

    # Read existing assignments and populate the dictionary
    if os.path.exists(ID_FILE):
        with open(ID_FILE, "r") as file:
            for line in file:
                parts = line.strip().split(",")
                if len(parts) == 3:
                    location_dir, grf_id, version = (
                        parts[0].strip(),
                        parts[1].strip(),
                        int(parts[2].strip()),
                    )
                    id_assignments[location_dir] = (grf_id, version)
                    id_used.add(int(grf_id[2:]))
    # Find the smallest unused ID in the existing sequence
    for i in range(1,
                   len(id_assignments) +
                   2):  # +2 to ensure a new ID if all are used sequentially
        if i not in id_used:
            id_gap = f"TA{i:02}"
            break
    # Assign ID and version
    if output_nml in id_assignments:
        grf_id, version = id_assignments[output_nml]
        version += 1  # Increment version if already exists
    else:
        grf_id = id_gap if id_gap else f"TA{len(id_assignments) + 1:02}"
        version = 1
    # Update the dictionary with the new or updated version
    id_assignments[output_nml] = (grf_id, version)

    # Write all data back to the file
    with open(ID_FILE, "w") as file:
        for location, (id_, ver) in id_assignments.items():
            file.write(f"{location},{id_},{ver}\n")
    return grf_id, version


def process_country_region(country_code, region_code, subregion_code):
    # Adjust file paths and names based on country and region
    country_file_code = country_code if country_code else "World"
    location_dir = f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names"
    output_dir = os.path.join(BASE_PATH, "Source_Files", location_dir)
    output_nml = os.path.join(
        output_dir,
        f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names.nml",
    )
    output_grf = os.path.join(
        output_dir,
        f"Taby_{country_file_code}{'_' + region_code if region_code else ''}{'_' + subregion_code if subregion_code else ''}_Town_Names.grf",
    )
    prepare_output_dir(output_dir, country_code, region_code, subregion_code)

    town_records, min_weight, scale, num_towns, lowest_population = process_town_data(
        country_code, region_code, subregion_code)

    # Assuming ID and other operations are similar for each pair
    grf_id, version = manage_id_assignments(location_dir)

    update_language_file(
        output_dir,
        country_code,
        region_code,
        subregion_code,
        version,
        num_towns,
        lowest_population,
    )

    write_nml_file(output_nml, grf_id, version, town_records, min_weight,
                   scale)
    if USE_OPENTTD_DIR:
        compile_and_deploy_grf(output_nml, output_grf, OPENTTD_DIR)
    else:
        if not os.path.exists(BASE_PATH + "/Output"):
            os.makedirs(BASE_PATH + "/Output", exist_ok=True)
        compile_and_deploy_grf(output_nml, output_grf, BASE_PATH + "\\Output")
    print(
        f"Processed {len(town_records)} towns for {country_code} {region_code} {subregion_code}"
    )


def take_input():
    data_input = []
    while True:
        user_input = input(
            "Enter a country code, region code, and subregion code separated by periods (e.g. GB.ENG.GLA for all names in London) or leave blank for the world. Enter 'done' when finished: "
        )
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
        country_name, region_name, subregion_name = get_country_region_subregion_names(
            country_code, region_code, subregion_code)
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
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH, exist_ok=True)
    if not os.path.exists(os.path.join(BASE_PATH, "Source_Files")):
        os.makedirs(os.path.join(BASE_PATH, "Source_Files"), exist_ok=True)
    for file in LIST_OF_DATA_FILES:
        file_text = file.replace(".zip", ".txt")
        if not os.path.exists(os.path.join(DATA_PATH, file_text)):
            download_data_files(file, DATA_URL + file)
            print(f"Downloaded {file}")
    if input("Do you want to use the data input list? (yes = y, no = n): "
             ) == "y":
        data_input = get_input(DATA_INPUT)
    else:
        data_input = take_input()
    print("Data input list:")
    print(data_input)
    i = 0
    for code in data_input:
        country_code, region_code, subregion_code = split_input(code)
        process_country_region(country_code, region_code, subregion_code)
        i += 1
        print(f"Processed {i} of {len(data_input)}")


if __name__ == "__main__":
    main()
