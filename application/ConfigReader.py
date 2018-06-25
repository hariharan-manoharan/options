import ConfigParser
import io
import os


fileDir = os.path.dirname(os.path.realpath('__file__'))
config_file_path = os.path.join(fileDir, 'config.INI')


def readConfig():
        frameworkConfig = {}
        # Load the configuration file
        with open(config_file_path) as f:
            sample_config = f.read()
        config = ConfigParser.RawConfigParser(allow_no_value=True)
        config.readfp(io.BytesIO(sample_config))

        for section in config.sections():
            for options in config.options(section):
                frameworkConfig.update({options:config.get(section, options)})

        return frameworkConfig