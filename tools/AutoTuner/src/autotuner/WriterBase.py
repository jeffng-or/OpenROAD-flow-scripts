#!/usr/bin/env python3

import os
import json

class WriterBase:
    """ Utility class to hold common methods used by writers """

    @staticmethod
    def _write_file(mod_content, path, output_file_name): # pragma: no cover
        file_name = os.path.join(os.path.abspath(path),output_file_name)
        with open(file_name, "w") as file:
            file.write(mod_content)
        return file_name
        
    @staticmethod
    def read_content_file(file_name): # pragma: no cover
        """ Utility function to read the content to be modified """
        
        content = None
        with open(file_name, "r") as f:
           content = f.read()
        return content

    @staticmethod
    def read_variable_file(file_name): # pragma: no cover
        """ 
        Utility function to read the variable JSON file and return the
        dictionary

        JSON is of the form:

            {
                "CLK_PERIOD": 1200,
                "UNCERTAINTY": 10,
                "IO_DELAY": 100,
                "LAYER_ADJUST": 0.25,
                "LAYER_ADJUSTmetal1": 0.25,
                "GR_SEED": 1234,
            }
        """
        
        variables = {}
        with open(file_name, "r") as f:
            variables = json.load(f)
        return variables
    
    
