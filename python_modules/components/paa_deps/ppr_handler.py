import logging
import os
import shutil
import attr #>=22.2.0

@attr.s
class PprHandler:

    """
    Prepares and handles python packaging repo with package-auto-assembler.
    """

    # inputs
    paa_dir = attr.ib(default=".paa")

    # processed
    logger = attr.ib(default=None)
    logger_name = attr.ib(default='PPR Handler')
    loggerLvl = attr.ib(default=logging.INFO)
    logger_format = attr.ib(default=None)

    def __attrs_post_init__(self):
        self._initialize_logger()

    def _initialize_logger(self):
        """
        Initialize a logger for the class instance based on the specified logging level and logger name.
        """

        if self.logger is None:
            logging.basicConfig(level=self.loggerLvl, format=self.logger_format)
            logger = logging.getLogger(self.logger_name)
            logger.setLevel(self.loggerLvl)

            self.logger = logger

    def _create_init_paa_dir(self, paa_dir : str):

        os.makedirs(paa_dir)

        with open(os.path.join(paa_dir, 'package_licenses.json'), 'w') as init_file:
            init_file.write("{}")

        with open(os.path.join(paa_dir, 'package_mapping.json'), 'w') as init_file:
            init_file.write("{}")

    def _create_empty_tracking_files(self, paa_dir : str):

        os.makedirs(os.path.join(paa_dir,'tracking'))

        with open(os.path.join(paa_dir,'tracking','lsts_package_versions.yml'),
            'w') as file:
            file.write("")

        log_file = open(os.path.join(paa_dir,'tracking','version_logs.csv'), 
        'a', 
        newline='', 
        encoding="utf-8")
        csv_writer = csv.writer(log_file)
        csv_writer.writerow(['Timestamp', 'Package', 'Version'])

    def _create_init_requirements(self, paa_dir : str):

        os.makedirs(os.path.join(paa_dir,'requirements'))

        init_requirements = [
            ### dev requirements for tools
            'python-dotenv==1.0.0',
            'stdlib-list==0.10.0',
            'pytest==7.4.3',
            'pylint==3.0.3',
            'mkdocs-material==9.5.30',
            'jupyter',
            'ipykernel',
            'tox',
            'tox-gh-actions',
            'package-auto-assembler'
        ]

        with open(os.path.join(paa_dir,'requirements', 'requirements_dev.txt'), 
        'w') as file:
            for req in init_requirements:
                file.write(req + '\n')

    def init_paa_dir(self, paa_dir : str = None):

        """
        Prepares .paa dir for packaging
        """

        if paa_dir is None:
            paa_dir = self.paa_dir

        try:

            if not os.path.exists(paa_dir):
                self._create_init_paa_dir(paa_dir = paa_dir)

            if not os.path.exists(os.path.join(paa_dir,'tracking')):
                self._create_empty_tracking_files(paa_dir = paa_dir)
            if not os.path.exists(os.path.join(paa_dir,'requirements')):
                self._create_init_requirements(paa_dir = paa_dir)
            if not os.path.exists(os.path.join(paa_dir,'release_notes')):
                os.makedirs(os.path.join(paa_dir,'release_notes'))
        except Exception as e:
            self.logger.warning("Failed to initialize paa dir!")
            self.logger.error(f"e")
            return False

        return True
            






