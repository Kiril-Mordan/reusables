import pytest
import yaml
import dill
from draft_modules.parameterframe import FileTypeHandler

# A list of tuples, each containing the paths to an input YAML file and its expected output YAML file
YAML_FILE_PATHS = [
    ("tests/parameterframe/example_configs/param_1.yaml", "tests/parameterframe/example_configs_output/param_1.yaml"),
    ("tests/parameterframe/example_configs/param_2.yaml", "tests/parameterframe/example_configs_output/param_2.yaml"),
    ("tests/parameterframe/example_configs/param_3.yaml", "tests/parameterframe/example_configs_output/param_3.yaml"),
    ("tests/parameterframe/example_configs/param_4.yaml", "tests/parameterframe/example_configs_output/param_4.yaml"),
    ("tests/parameterframe/example_configs/param_5.yaml", "tests/parameterframe/example_configs_output/param_5.yaml")

]

TXT_FILE_PATHS = [
    ("tests/parameterframe/example_configs/param_6.txt", "tests/parameterframe/example_configs_output/param_6.txt"),
    ("tests/parameterframe/example_configs/param_7.txt", "tests/parameterframe/example_configs_output/param_7.txt"),
    ("tests/parameterframe/example_configs/param_8.txt", "tests/parameterframe/example_configs_output/param_8.txt"),
    ("tests/parameterframe/example_configs/param_9.txt", "tests/parameterframe/example_configs_output/param_9.txt"),
    ("tests/parameterframe/example_configs/param_10.txt", "tests/parameterframe/example_configs_output/param_10.txt")
]

DILL_FILE_PATHS = [
    ("tests/parameterframe/example_configs/param_11.dill", "tests/parameterframe/example_configs_output/param_11.dill"),
    ("tests/parameterframe/example_configs/param_14.dill", "tests/parameterframe/example_configs_output/param_14.dill"),
    ("tests/parameterframe/example_configs/param_15.dill", "tests/parameterframe/example_configs_output/param_15.dill")
]



def load_yaml_file(file_path):
    """Utility function to load a YAML file and return its content."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

@pytest.mark.parametrize("input_path,expected_output_path", YAML_FILE_PATHS)
def test_compare_yaml_files(input_path, expected_output_path):
    """
    Test function to compare the content of two yaml files.
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )


    input_content = load_yaml_file(input_path)
    expected_output_content = load_yaml_file(expected_output_path)

    assert input_content == expected_output_content, f"yaml content mismatch between {input_path} and {expected_output_path}"

@pytest.mark.parametrize("input_path,expected_output_path", TXT_FILE_PATHS)
def test_compare_txt_files(input_path, expected_output_path):
    """
    Test function to compare the content of two txt files.
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )

    with open(input_path, 'r') as file:
        input_content = file.read()

    with open(expected_output_path, 'r') as file:
        expected_output_content = file.read()

    assert input_content == expected_output_content, f"txt content mismatch between {input_path} and {expected_output_path}"

@pytest.mark.parametrize("input_path,expected_output_path", DILL_FILE_PATHS)
def test_compare_dill_files(input_path, expected_output_path):
    """
    Test function to compare the content of two dill files.
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )


    with open(input_path, 'rb') as file:
        input_content = dill.load(file)

    with open(expected_output_path, 'rb') as file:
        expected_output_content = dill.load(file)

    assert input_content == expected_output_content, f"dill content mismatch between {input_path} and {expected_output_path}"


@pytest.mark.parametrize("input_path,expected_output_path",
                         [("tests/parameterframe/example_configs/param_12.dill",
                           "tests/parameterframe/example_configs_output/param_12.dill")])
def test_load_complex_instance_from_reconstructed_dill(input_path, expected_output_path):

    """
    Test if complex funtion is reconstructed from dill
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )

    with open(expected_output_path, 'rb') as file:
        expected_output_content = dill.load(file)

    assert expected_output_content.name == "ComplexExample"
    assert expected_output_content.display_info().startswith("Name: ComplexExample")

@pytest.mark.parametrize("input_path,expected_output_path",
                         [("tests/parameterframe/example_configs/param_13.dill",
                           "tests/parameterframe/example_configs_output/param_13.dill")])
def test_load_function_from_reconstructed_dill(input_path, expected_output_path):

    """
    Test if function was reconstructed from dill
    """

    fth = FileTypeHandler(file_path = input_path)
    fth.process_file()

    parameter_id = fth.parameter_id
    parameter_attributes_list = fth.parameter_attributes_list
    attribute_values_list = fth.attribute_values_list

    fth2 = FileTypeHandler()

    fth2.reconstruct_file(
        file_path = expected_output_path,
        parameter_id = parameter_id,
        parameter_attributes_list = parameter_attributes_list,
        attribute_values_list = attribute_values_list
    )

    with open(expected_output_path, 'rb') as file:
        sample_function = dill.load(file)


    assert callable(sample_function)
    assert sample_function(2) == 2*2 + 3*2 + 5  # Testing the function with an input of 2
