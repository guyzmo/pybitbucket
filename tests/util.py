# -*- coding: utf-8 -*-
from os import path


def data_from_file(directory, filename):
    filepath = path.join(directory, filename)
    with open(filepath) as f:
        data = f.read()
    return data
