# Steps to add a new version:

## antarest/study/model.py
* Add template to STUDY_REFERENCE_TEMPLATE
* Update NEW_DEFAULT_STUDY_VERSION

## resources/
* Add new study template  zipped here

## antarest/study/business/config_management.py
* Add eventual new output variables (OutputVariable class) 
* Update method ConfigManager.get_output_variable()

Output_variable list: https://antares-simulator.readthedocs.io/en/latest/reference-guide/05-output_files/

## antarest/study/storage/rawstudy/model/filesystem/root/...
* Add eventual new files, new fields in files

## antarest/study/storage/variantstudy/model/command
* Edit concerned commands