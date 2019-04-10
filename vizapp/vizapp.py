import inspect

import numpy as np


class VizApp:

    def __init__(self):

        self._history = []

        self._3d_data = {}
        self._2d_data = {}
        self._1d_data = {}

        self._3d_processing = {}
        self.add_3d_processing("Median Collapse", lambda x: np.nanmedian(x, axis=0), [])
        self.add_3d_processing("Mean Collapse", lambda x: np.nanmean(x, axis=0), [])

        self._2d_processing = {}

        self._1d_processing = {}

    # ---------------------------------------------------------------
    #
    #  processing
    #
    # ---------------------------------------------------------------

    def add_3d_processing(self, name, func, parameters):
        """

        :param name: str name to display
        :param func: method  method to run
        :param parameters: tuple - list of parameters
        :return: none
        """

        if not isinstance(name, str):
            raise TypeError('add_3d_processing: name, {}, must be a string')

        if not inspect.isfunction(func):
            raise TypeError('add_3d_processing: func must be a method')

        if not isinstance(parameters, list):
            raise TypeError('add_3d_processing: parameters must be a list')

        if parameters:
            if any([not isinstance(x, tuple) or not len(x) == 2 for x in parameters]):
                raise TypeError('add_3d_processing: each parameter must be a parameter name and default value')

        self._3d_processing[name] = {
            'method': func,
            'parameters': parameters
        }

    def get_3d_processing(self, name=None):
        """
        Get the list of types of processing that can be done on a 3D dataset

        :return: list - list of keys to the types of processing
        """
        # TODO: Fix the above description

        if name is not None:
            return self._3d_processing[name]
        else:
            return list(self._3d_processing.keys())

    # TODO: Lots of things here: Need parameters, add result to dict
    def process_3d(self, name, data, processor):
        self._3d_data[name] = processor(data)

    def add_2d_processing(self, name, func):
        self._2d_processing[name] = func

    def get_2d_processing(self):
        return self._2d_processing

    def add_1d_processing(self, name, func):
        self._1d_processing[name] = func

    def get_1d_processing(self):
        return self._1d_processing

    # ---------------------------------------------------------------
    #
    #  data
    #
    # ---------------------------------------------------------------

    def add_data(self, name, data):
        """
        Add data to the vizapp object. This can be 1D, 2D or 3D.

        :param name: Name of the dataset, used as the key.
        :param data: Numpy array of data.
        :return:
        """
        if len(data.shape) == 3:
            self._3d_data[name] = data
        if len(data.shape) == 2:
            self._2d_data[name] = data

    def get_data(self, name):
        """
        Get the data from one of the data containers.

        :param name: str or int  key for lookup
        :return:
        """

        if isinstance(name, int):
            key = list(self._3d_data.keys())[0]

            if not key:
                return None

            return self._3d_data[key]
        elif isinstance(name, str):
            return self._3d_data[name]
        else:
            raise('get_data takes an int or string.')
