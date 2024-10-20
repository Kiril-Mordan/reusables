from python_modules.package_auto_assembler import RequirementsHandler
import pytest


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
    }

@pytest.mark.parametrize("module_filepath,expected_requirements", [
    ("./tests/package_auto_assembler/other/t_module_1.py", ['### test_module_1.py',
 'dill==5.0.1',
 'pandas==2.1.1',
 'attrs>=22.2.0',
 'sentence-transformers==2.2.2',
 'scikit-learn==1.3.1']),
    ("./tests/package_auto_assembler/other/t_module_2.py", ['### test_module_2.py',
 'google-auth-oauthlib',
 'google',
 'google-api-python-client']),

 ("./tests/package_auto_assembler/other/t_module_3.py" , ['### test_module_3.py',
 'numpy==1.26.0',
 'dill==0.3.7',
 'attrs>=22.2.0',
 'hnswlib==0.8.0',
 'sentence-transformers==2.2.2']),

 ("./tests/package_auto_assembler/other/t_module_4.py" , ['### test_module_4.py',
 'nbformat',
 'stdlib-list',
 'nbconvert',
 'pyyaml',
 'pandas==2.1.1',
 'attrs>=22.2.0']),
 ("./tests/package_auto_assembler/other/t_module_5.py" , ['### test_module_5.py', 'dill==0.3.7', 'attrs>=22.2.0']),
 ("./tests/package_auto_assembler/other/t_module_6.py", ['### test_module_6.py',
 'dill[test]==5.0.1',
 'pandas[all]==2.1.1',
 'attrs>=22.2.0',
 'scikit-learn==1.3.1']),
    ("./tests/package_auto_assembler/other/t_module_7.py", ['### test_module_7.py',
 'google-auth-oauthlib',
 'google-api-python-client',
 'fastapi[all]',
 'uvicorn[all]']),

 ("./tests/package_auto_assembler/other/t_module_8.py" , ['### test_module_8.py',
 'numpy==1.26.0',
 'dill==0.3.7',
 'attrs>=22.2.0',
 'hnswlib==0.8.0',
 'sentence-transformers==2.2.2',
 'fastapi',
 'uvicorn[all]',
 'tensorflow-gpu ; platform_system == "Linux"'])
])
def test_requirements_extractions(module_filepath, expected_requirements):
   rh = RequirementsHandler(module_filepath=module_filepath,
                         package_mappings = package_mappings)


   reqs = rh.extract_requirements()[0] + rh.extract_requirements()[1]

   print(reqs)

   assert all([ req in expected_requirements for req in reqs]) == True