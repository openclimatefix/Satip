""" Data store utils"""


def dateset_it_to_filename(dataset_id: str, tailor_id: str, dir) -> str:
    """Change a dataset id to a file name

    e.g 'MSG4-SEVI-MSG15-0100-NA-20221201161242.889000000Z-NA'
    to MSG4-SEVI-MSG15-0100-NA-20221201161242.889000000Z.NA

    :param dataset_id: dataset id
    :param tailor_id: taylor id
    :param dir: directory where to save the file
    :return: filename
    """

    # these names are very sensitive, consider carefully when changing
    if 'HRSEVIRI' not in tailor_id:
        filename = f"{dir}/{dataset_id}_{tailor_id}.nat"
    else:
        filename = f"{dir}/{dataset_id}_EPCT_{tailor_id}"

    return filename
