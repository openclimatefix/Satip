""" Data store utils"""


def dateset_it_to_filename(dataset_id:str, dir)->str:
    """ Change a dataset id to a file name

    e.g 'MSG4-SEVI-MSG15-0100-NA-20221201161242.889000000Z-NA' to MSG4-SEVI-MSG15-0100-NA-20221201161242.889000000Z.NA


    """

    dataset_id = f'{dir}/{dataset_id[-3]}.NA'

    return dataset_id