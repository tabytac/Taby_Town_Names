# Taby Town Names

Taby Town Names is a project that aims to provide a collection of unique town names for the OpenTTD game. All town names are generated using the given Python script and are based on the names of real towns and cities around the world using the database provided by the [GeoNames](http://www.geonames.org/) project.

## Table of Contents

- [Installation](#installation)
- [License](#license)

## Installation

To install Taby Town Names, follow these steps:

1. Navigate to the Source_Files directory and either choose a pre-generated NewGRF file or generate a new one using the provided Python script.
   - To generate a new NewGRF file, download the Python script and run it using the following command:
     ```
     python generate_newgrf.py
     ```
   - The generated NewGRF file will be saved in the NewGRF directory.
3. Move the NewGRF file to the OpenTTD data directory.
   - The default data directory locations are:
     - Windows: `C:\Users\<username>\Documents\OpenTTD`
     - macOS: `~/Documents/OpenTTD`
     - Linux: `~/.openttd`
4. Enable the NewGRF file in the OpenTTD game settings.


## License
The Python script and all generated files in this project are licensed under the GPL-2.0 License. See [LICENSE](LICENSE) for more information.

The GeoNames database is licensed under Creative Commons Attribution 4.0 International. To view a copy of this license, visit [here](https://creativecommons.org/licenses/by/4.0/).

The countries.csv file, taken from the [mledoze/countries](https://github.com/mledoze/countries) repository, is used to map country names with their respective demonyms, and is licensed under the [ODbL License](https://opendatacommons.org/licenses/odbl/1-0/).