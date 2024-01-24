from python_modules.package_auto_assembler import RequirementsHandler
import pytest

@pytest.mark.parametrize("module_filepath,expected_requirements", [
    ("./tests/package_auto_assembler/test_module_1.py", ['### test_module_1.py',
 'dill==5.0.1',
 'pandas',
 'attrs>=22.2.0',
 'sentence-transformers==2.2.2',
 'scikit-learn==1.3.1']),
    ("./tests/package_auto_assembler/test_module_2.py", ['### test_module_2.py',
 'google-auth-oauthlib',
 'google',
 'google-api-python-client']),

 ("./tests/package_auto_assembler/test_module_3.py" , ['### test_module_3.py',
 'numpy',
 'dill==0.3.7',
 'attrs>=22.2.0',
 'hnswlib',
 'sentence-transformers==2.2.2']),

 ("./tests/package_auto_assembler/test_module_4.py" , ['### test_module_4.py',
 'nbformat',
 'stdlib-list',
 'nbconvert',
 'pyyaml',
 'pandas',
 'attrs>=22.2.0']),

 ("./tests/package_auto_assembler/test_module_5.py" , ['### test_module_5.py', 'dill==0.3.7', 'attrs>=22.2.0'])
    # Add more cases for other output_types
])
def test_requirements_extractions(module_filepath, expected_requirements):
    rh = RequirementsHandler(module_filepath=module_filepath,
                         package_mappings = {
    "PIL": "Pillow",
    "bs4": "beautifulsoup4",
    "fitz": "PyMuPDF",
    "attr": "attrs",
    "dotenv": "python-dotenv",
    "googleapiclient": "google-api-python-client",
    "google_auth_oauthlib" : "google-auth-oauthlib",
    "sentence_transformers": "sentence-transformers",
    "flask": "Flask",
    "stdlib_list": "stdlib-list",
    "sklearn" : "scikit-learn",
    "yaml" : "pyyaml",
    "package_auto_assembler" : "package-auto-assembler"
    })
    assert all([ req in expected_requirements for req in rh.extract_requirements()]) == True