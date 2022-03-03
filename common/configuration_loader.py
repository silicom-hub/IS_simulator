from configparser import ConfigParser


def parse_values_list(file, section, key):
    """ Read ini file and returns available workstations functions

    :param file: File to be parsed
    :type file: str
    :param section: Section targeted
    :type section: str
    :param key: Parameter to be read
    :type key: str
    :return: Read values list
    :rtype: list
    """
    config = ConfigParser()
    config.read(file)
    config.sections()
    values = config[section][key].split(", ")
    return values


def parse_value(file, section, key):
    """ Read ini file and returns unique value

    :param file: File to be parsed
    :type file: str
    :param section: Section targeted
    :type section: str
    :param key: Parameter to be read
    :type key: str
    :return: Read value
    :rtype: str
    """
    config = ConfigParser()
    config.read(file)
    config.sections()
    value = config[section][key]
    return value

# Tests
if __name__ == '__main__':
    test_lists = parse_values_list("workstations/common.ini", "FUNCTIONS", "common")
    print(test_lists)

    test_value = parse_value("workstations/common.ini", "FUNCTIONS", "elk")
    print(test_value)
