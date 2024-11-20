#!/usr/bin/env python3

import os
import sys
import json
import unittest
import ray
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "autotuner"))
from ParamConfigReader import ParamConfigReader

class ParamConfigReaderTest(unittest.TestCase):
    """ ParamConfigReader unit tests """
    
    def setUp(self):
        """ Defines some commonly used variables """

        # Directory where this file is located, so that we can find
        # the external files
        self._config_file_dir_name = os.path.dirname(__file__)
        
        # Basic test case that includes
        # int
        #   step 0
        #   step 1
        #   step > 1
        # float
        #   step 0
        #   step 1
        #   step 1.0
        #   step > 1
        self._tune_data = """
        {
            "CORE_MARGIN": {
                "type": "int",
                "minmax": [
                    2,
                    2
                ],
                "step": 0
            },
            "CELL_PAD_IN_SITES_GLOBAL_PLACEMENT": {
                "type": "int",
                "minmax": [
                    1,
                    3
                ],
                "step": 1
            },
            "CTS_CLUSTER_SIZE": {
                "type": "int",
                "minmax": [
                    10,
                    200
                ],
                "step": 1
            },
            "CTS_CLUSTER_DIAMETER": {
                "type": "int",
                "minmax": [
                    20,
                    400
                ],
                "step": 100
            },
            "CORE_ASPECT_RATIO": {
                "type": "float",
                "minmax": [
                    0.5,
                    2.0
                ],
                "step": 0
            },
            "_SDC_CLK_PERIOD": {
                "type": "float",
                "minmax": [
                    14.0,
                    16.0
                ],
                "step": 1
            },
            "PLACE_DENSITY_LB_ADDON": {
                "type": "float",
                "minmax": [
                    1.0,
                    5.0
                ],
                "step": 1.0
            },
            "CTS_BUF_DISTANCE": {
                "type": "float",
                "minmax": [
                    1.0,
                    10.0
                ],
                "step": 4.0
            }
        }
        """

        # Test case for param config with no minmax
        self._missing_minmax_data = """
        {
            "CTS_CLUSTER_SIZE": {
                "type": "int",
                "minmax": [
                    10,
                    200
                ],
                "step": 1
            },
            "_SDC_CLK_PERIOD": {
                "type": "float",
                "step": 0
            }
        }
        """

        # Test case for empty file paths
        self._empty_paths = """
        {
            "CORE_MARGIN": {
                "type": "int",
                "minmax": [
                    2,
                    2
                ],
                "step": 0
            },
            "_SDC_FILE_PATH": "",
            "_FR_FILE_PATH": ""
        }
        """

        # Test case for a non-dictionary value
        self._non_dict_value = """
        {
            "CORE_MARGIN": {
                "type": "int",
                "minmax": [
                    2,
                    2
                ],
                "step": 0
            },
            "SINGLE_VALUE": 10
        }
        """
        
    def config_array_to_dict(self, input_array):
        """ 
        Converts an array of elements to a dictionary using the element's name
        value as the key
        """
        ret = {}
        for item in input_array:
            ret[item["name"]] = item
        return ret

    def assertCategoricalEqual(self, config, expected):
        """ 
        Asserts that the ray.tune.search.Categorical in the config object's
        values slot is equal to the expected value
        """

        for key in ["name", "type", "value_type"]:
            self.assertEqual(config[key], expected[key])
        self.assertEqual(config["values"].domain_str, expected["values"])
    
    def test_sweep_mode(self):
        """
        Tests the param config extracted for sweep mode

        TODO: add all supported element types
        """
        
        config_json = """
        {
            "best_result": "bogus",
            "_SDC_FILE_PATH": "files/simple.sdc",
            "_SDC_CLK_PERIOD": {
                "type": "float",
                "minmax": [
                    14.0,
                    16.0
                ],
                "step": 0
            },
            "CORE_MARGIN": {
                "type": "int",
                "minmax": [
                    2,
                    2
                ],
                "step": 0
            },
            "_FR_FILE_PATH": "files/simple_fastroute.tcl",
            "_FR_GR_OVERFLOW": {
                "type": "int",
                "minmax": [
                    1,
                    1
                ],
                "step": 0
            }
        }
        """
        json_data = json.loads(config_json)
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "sweep", "N/A", self._config_file_dir_name)
        self.assertIsNotNone(config)
        self.assertIsNotNone(sdc_data)
        self.assertTrue(len(sdc_data) > 0)
        self.assertIsNotNone(fr_data)
        self.assertTrue(len(fr_data) > 0)
        # sweep returns a dict
        self.assertEqual(len(config.keys()), 3)
        self.assertEqual(config["_SDC_CLK_PERIOD"], [14.0, 16.0, 0])
        self.assertEqual(config["_FR_GR_OVERFLOW"], [1, 1, 0])
        self.assertEqual(config["CORE_MARGIN"], [2, 2, 0])        

    def test_tune_ax(self):
        """
        Tests creating each of the supported parameter config types when used
        with tune mode and AX algorithm
        """
        
        json_data = json.loads(self._tune_data)
        # TODO: put CTS_CLUSTER_DIAMETER back in once randint issue is resolved
        del json_data["CTS_CLUSTER_DIAMETER"]
        # tune ax returns an array of dicts
        (config_array, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "ax", self._config_file_dir_name)
        self.assertEqual(len(config_array), 7)
        self.assertEqual(sdc_data, "")
        self.assertEqual(fr_data, "")
        config = self.config_array_to_dict(config_array)
        self.assertCategoricalEqual(config["_SDC_CLK_PERIOD"], {"name": "_SDC_CLK_PERIOD", "type": "choice", "value_type": "float", "values": "[14.0, 15.0]"})
        self.assertEqual(config["CORE_MARGIN"], {"name": "CORE_MARGIN", "type": "fixed", "value": 2})
        self.assertEqual(config["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"], {"name": "CELL_PAD_IN_SITES_GLOBAL_PLACEMENT", "type": "range", "bounds": [1, 3], "value_type": "int"})
        self.assertEqual(config["CTS_CLUSTER_SIZE"], {"name": "CTS_CLUSTER_SIZE", "type": "range", "bounds": [10, 200], "value_type": "int"})
        # TODO: re-enable this check once randint issue is resolved
        #self.assertEqual(config["CTS_CLUSTER_DIAMETER"], {"name": "CTS_CLUSTER_DIAMETER", "type": "range", "bounds": [10, 200], "value_type": "int"})
        self.assertEqual(config["CORE_ASPECT_RATIO"], {"name": "CORE_ASPECT_RATIO", "type": "range", "bounds": [0.5, 2.0], "value_type": "float"})
        self.assertCategoricalEqual(config["PLACE_DENSITY_LB_ADDON"], {"name": "PLACE_DENSITY_LB_ADDON", "type": "choice", "value_type": "float", "values": "[1.0, 2.0, 3.0, 4.0]"})
        self.assertEqual(config["CTS_BUF_DISTANCE"], {"name": "CTS_BUF_DISTANCE", "type": "range", "value_type": "float", "bounds": [1.0, 10.0]})

    def test_tune_pbt(self):
        """
        Tests creating each of the supported parameter config types when used
        with tune mode and PBT algorithm
        """
        
        json_data = json.loads(self._tune_data)
        # tune pbx returns a dict of key: value pairs
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "pbt", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 8)
        self.assertEqual(sdc_data, "")
        self.assertEqual(fr_data, "")
        self.assertEqual(config["_SDC_CLK_PERIOD"].domain_str, "(14.0, 16.0)")
        self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")
        self.assertEqual(config["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"].domain_str, "(1, 3)")
        self.assertEqual(config["CTS_CLUSTER_SIZE"].domain_str, "(10, 200)")
        self.assertEqual(config["CTS_CLUSTER_DIAMETER"].domain_str, "(20, 400)")
        self.assertEqual(config["CORE_ASPECT_RATIO"].domain_str, "(0.5, 2.0)")
        self.assertEqual(config["PLACE_DENSITY_LB_ADDON"].domain_str, "(1.0, 5.0)")
        self.assertEqual(config["CTS_BUF_DISTANCE"].domain_str, "(1.0, 10.0)")
        
    def test_tune_hyperopt_optuna(self):
        """
        Tests creating each of the supported parameter config types when used
        with tune mode and hyperopt or optuna algorithms
        """

        json_data = json.loads(self._tune_data)
        # tune hyperopt & tune optuna return a dict of key: value pairs
        for algorithm in ["hyperopt", "optuna"]:
            (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", algorithm, self._config_file_dir_name)
            self.assertEqual(len(config.keys()), 8)
            self.assertEqual(sdc_data, "")
            self.assertEqual(fr_data, "")
            self.assertEqual(config["_SDC_CLK_PERIOD"].domain_str, "[14.0, 15.0]")
            self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")
            self.assertEqual(config["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"].domain_str, "(1, 3)")
            self.assertEqual(config["CTS_CLUSTER_SIZE"].domain_str, "(10, 200)")

            self.assertEqual(config["CTS_CLUSTER_DIAMETER"].domain_str, "[20, 120, 220, 320]")
            self.assertEqual(config["CORE_ASPECT_RATIO"].domain_str, "(0.5, 2.0)")
            self.assertEqual(config["PLACE_DENSITY_LB_ADDON"].domain_str, "[1.0, 2.0, 3.0, 4.0]")
            self.assertEqual(config["CTS_BUF_DISTANCE"].domain_str, "[1.0, 5.0, 9.0]")
        
    def test_tune_random_no_CPISDP(self):
        """
        Tests creating each of the supported parameter config types when used
        with tune mode and random algorithm. Content doesn't include 
        CELL_PAD_IN_SITES_DETAIL_PLACEMENT
        """
        
        json_data = json.loads(self._tune_data)
        # tune random returns a dict of key: value pairs
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "random", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 8)
        self.assertEqual(sdc_data, "")
        self.assertEqual(fr_data, "")
        self.assertEqual(config["_SDC_CLK_PERIOD"].domain_str, "[14.0, 15.0]")
        self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")
        self.assertEqual(config["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"].domain_str, "(1, 3)")
        self.assertEqual(config["CTS_CLUSTER_SIZE"].domain_str, "(10, 200)")
        self.assertEqual(config["CTS_CLUSTER_DIAMETER"].domain_str, "[20, 120, 220, 320]")
        self.assertEqual(config["CORE_ASPECT_RATIO"].domain_str, "(0.5, 2.0)")
        self.assertEqual(config["PLACE_DENSITY_LB_ADDON"].domain_str, "[1.0, 2.0, 3.0, 4.0]")
        self.assertEqual(config["CTS_BUF_DISTANCE"].domain_str, "[1.0, 5.0, 9.0]")

    def test_tune_random_CPISDP_step_one(self):
        """
        Tests creating each of the supported parameter config types when used
        with tune mode and random algorithm. Content includes
        CELL_PAD_IN_SITES_DETAIL_PLACEMENT with step == 1
        """
        
        json_data = json.loads(self._tune_data)
        json_data["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"] = {
            "type": "int",
            "minmax": [
                1,
                3
            ],
            "step": 1
        }
        # tune random returns a dict of key: value pairs
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "random", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 9)
        self.assertEqual(sdc_data, "")
        self.assertEqual(fr_data, "")
        self.assertEqual(config["_SDC_CLK_PERIOD"].domain_str, "[14.0, 15.0]")
        self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")
        self.assertEqual(config["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"].domain_str, "(1, 3)")
        self.assertEqual(config["CTS_CLUSTER_SIZE"].domain_str, "(10, 200)")
        self.assertEqual(config["CTS_CLUSTER_DIAMETER"].domain_str, "[20, 120, 220, 320]")
        self.assertEqual(config["CORE_ASPECT_RATIO"].domain_str, "(0.5, 2.0)")
        self.assertEqual(config["PLACE_DENSITY_LB_ADDON"].domain_str, "[1.0, 2.0, 3.0, 4.0]")
        # since the config value is a lambda, best we can do is verify the type
        self.assertIsInstance(config["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"],
                              ray.tune.search.sample.Function)
        self.assertEqual(config["CTS_BUF_DISTANCE"].domain_str, "[1.0, 5.0, 9.0]")
    def test_tune_random_CPISDP_step_zero(self):
        """
        Tests creating each of the supported parameter config types when used
        with tune mode and random algorithm. Content includes
        CELL_PAD_IN_SITES_DETAIL_PLACEMENT with step == 0
        
        TODO: apply_condition hits a div by zero exception if step == 0, since
        there's no code to protect against step == 0. step == -1 passes this 
        test
        """
        
        json_data = json.loads(self._tune_data)
        json_data["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"] = {
            "type": "int",
            "minmax": [
                1,
                3
            ],
            "step": 0
        }
        # tune random returns a dict of key: value pairs
        # TODO: remove or replace assert when error is handled gracefully
        with self.assertRaises(ZeroDivisionError):
            (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "random", self._config_file_dir_name)
        
    def test_tune_random_CPISDP_step_gt_one(self):
        """
        Tests creating each of the supported parameter config types when used
        with tune mode and random algorithm. Content includes
        CELL_PAD_IN_SITES_DETAIL_PLACEMENT with step > 1
        """
        
        json_data = json.loads(self._tune_data)
        json_data["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"] = {
            "type": "int",
            "minmax": [
                1,
                6
            ],
            "step": 2
        }
        # tune random returns a dict of key: value pairs
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "random", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 9)
        self.assertEqual(sdc_data, "")
        self.assertEqual(fr_data, "")
        self.assertEqual(config["_SDC_CLK_PERIOD"].domain_str, "[14.0, 15.0]")
        self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")
        self.assertEqual(config["CELL_PAD_IN_SITES_GLOBAL_PLACEMENT"].domain_str, "(1, 3)")
        self.assertEqual(config["CTS_CLUSTER_SIZE"].domain_str, "(10, 200)")
        self.assertEqual(config["CTS_CLUSTER_DIAMETER"].domain_str, "[20, 120, 220, 320]")
        self.assertEqual(config["CORE_ASPECT_RATIO"].domain_str, "(0.5, 2.0)")
        self.assertEqual(config["PLACE_DENSITY_LB_ADDON"].domain_str, "[1.0, 2.0, 3.0, 4.0]")
        # since the config value is a lambda, best we can do is verify the type
        self.assertIsInstance(config["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"],
                              ray.tune.search.sample.Function)
        self.assertEqual(config["CTS_BUF_DISTANCE"].domain_str, "[1.0, 5.0, 9.0]")
    def test_sweep_param_missing_minmax(self):
        """
        Tests error condition when sweep is given a parameter without a minmax
        field

        TODO: this bombs out in read_sweep, which assumes that the param
        will have a minmax
        """
        
        # TODO: we should exit gracefully and not stack, so eventually replace
        # or remove this assertRaises
        with self.assertRaises(KeyError):
            json_data = json.loads(self._missing_minmax_data)
            (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "sweep", "N/A", self._config_file_dir_name)
        
    def test_tune_ax_param_missing_minmax(self):
        """
        Tests error condition when tune with AX is given a parameter without a
        minmax field

        TODO: Should we be inserting a None value into the array. Also, there
        was no warning or error indicating that we got bad data
        """
        
        json_data = json.loads(self._missing_minmax_data)
        # tune ax returns an array of dicts
        (config_array, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "ax", self._config_file_dir_name)
        self.assertEqual(len(config_array), 2)
        if config_array[0] == None:
            cluster_size_index = 1
        else:
            cluster_size_index = 0
        self.assertEqual(config_array[cluster_size_index], {"name": "CTS_CLUSTER_SIZE", "type": "range", "bounds": [10, 200], "value_type": "int"})

    def test_tune_pbt_param_missing_minmax(self):
        """
        Tests error condition when tune with PBT is given a parameter without a
        minmax field

        TODO: is adding a key with a None value what we want or should the code
        not add the parameter to the dict. Either way, there's no error message
        that bogus data was given to us
        """
        
        json_data = json.loads(self._missing_minmax_data)
        # tune pbt returns a dict of key: value pairs
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "pbt", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 2)
        self.assertIsNone(config["_SDC_CLK_PERIOD"])
        self.assertEqual(config["CTS_CLUSTER_SIZE"].domain_str, "(10, 200)")
        
    def test_tune_hyperopt_optuna_random_param_missing_minmax(self):
        """
        Tests error condition when tune with hyperopt, optuna, or random is
        given a parameter without a minmax field

        TODO: this bombs out in read_tune, which assumes that the param
        will have a minmax
        """
        
        json_data = json.loads(self._missing_minmax_data)
        # tune hyperopt & tune optuna return a dict of key: value pairs
        for algorithm in ["hyperopt", "optuna", "random"]:
            # TODO: we should exit gracefully and not stack, so eventually
            # replace or remove this assertRaises
            with self.assertRaises(KeyError):
                (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", algorithm, self._config_file_dir_name)

    def test_read_content_no_file(self):
        """ Tests case where we call read_content on a non-existent file """
        
        file_name = "constraint.sdc"
        content = ParamConfigReader.read_content(file_name)
        self.assertEqual(content, "")

    def test_sweep_empty_file_paths(self):
        """ 
        Tests case the file paths are empty and we're using sweep
        """
        
        json_data = json.loads(self._empty_paths)
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "sweep", "N/A", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 3)
        self.assertEqual(config["_SDC_FILE_PATH"], "")
        self.assertEqual(config["_FR_FILE_PATH"], "")
        self.assertEqual(config["CORE_MARGIN"], [2, 2, 0])        

    def test_tune_ax_empty_file_paths(self):
        """ 
        Tests case the file paths are empty and we're using tune AX
        """
        
        json_data = json.loads(self._empty_paths)
        (config_array, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "ax", self._config_file_dir_name)
        self.assertEqual(len(config_array), 1)
        config = self.config_array_to_dict(config_array)
        self.assertEqual(config["CORE_MARGIN"], {"name": "CORE_MARGIN", "type": "fixed", "value": 2})
        
    def test_tune_pbt_empty_file_paths(self):
        """ 
        Tests case the file paths are empty and we're using tune PBT
        """
        
        json_data = json.loads(self._empty_paths)
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "pbt", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 1)
        self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")
        
    def test_tune_hyperopt_optuna_empty_file_paths(self):
        """ 
        Tests case the file paths are empty and we're using tune hyperopt,
        optuna or random
        """
        
        json_data = json.loads(self._empty_paths)
        for algorithm in ["hyperopt", "optuna", "random"]:
            (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", algorithm, self._config_file_dir_name)
            self.assertEqual(len(config.keys()), 3)
            self.assertEqual(config["_SDC_FILE_PATH"], "")
            self.assertEqual(config["_FR_FILE_PATH"], "")
            self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")


    def test_sweep_non_dict_value(self):
        """ 
        Tests case where there's a non-dictionary value in the param config
        """
        
        json_data = json.loads(self._non_dict_value)
        (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "sweep", "N/A", self._config_file_dir_name)
        self.assertEqual(len(config.keys()), 2)
        self.assertEqual(config["CORE_MARGIN"], [2, 2, 0])
        self.assertEqual(config["SINGLE_VALUE"], 10)
            
    def test_tune_ax_non_dict_value(self):
        """ 
        Tests case where there's a non-dictionary value in the param config and
        we're using tune AX

        TODO: graceful error handling and error message
        """
        
        json_data = json.loads(self._non_dict_value)
        with self.assertRaises(TypeError):
            (config_array, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "ax", self._config_file_dir_name)
        
    def test_tune_pbt_non_dict_value(self):
        """ 
        Tests case where there's a non-dictionary value in the param config and
        we're using tune PBT

        TODO: graceful error handling and error message
        """
        
        json_data = json.loads(self._non_dict_value)
        with self.assertRaises(TypeError):
            (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", "pbt", self._config_file_dir_name)
        
    def test_tune_hyperopt_optuna_non_dict_value(self):
        """ 
        Tests case where there's a non-dictionary value in the param config and
        we're using tune hyperopt, optuna or random
        """
        
        json_data = json.loads(self._non_dict_value)
        for algorithm in ["hyperopt", "optuna", "random"]:
            (config, sdc_data, fr_data) = ParamConfigReader.read_config(json_data, "tune", algorithm, self._config_file_dir_name)
            self.assertEqual(len(config.keys()), 2)
            self.assertEqual(config["CORE_MARGIN"].domain_str, "[2, 2]")
            self.assertEqual(config["SINGLE_VALUE"], 10)

    def test_read_tune_unsupported_type(self):
        """ Tests read_tune directly when given an unsupported type """
        config_json = """
        {
            "DIE_AREA": {
                "type": "string",
                "minmax": [
                    "0 0 2000 2000",
                    "0 0 1000 1000"
                ]
            }
        }
        """
        json_data = json.loads(config_json)
        tune_val = ParamConfigReader.read_tune(json_data["DIE_AREA"])
        self.assertIsNone(tune_val)

    def test_read_config_file(self):
        """ Tests read_config_file iterface with sweep mode """
        
        (config, sdc_data, fr_data) = ParamConfigReader.read_config_file("files/simple_autotuner.json", "sweep", "N/A")
        self.assertIsNotNone(config)
        self.assertIsNotNone(sdc_data)
        self.assertTrue(len(sdc_data) > 0)
        self.assertIsNotNone(fr_data)
        self.assertTrue(len(fr_data) > 0)
        # sweep returns a dict
        self.assertEqual(len(config.keys()), 3)
        self.assertEqual(config["_SDC_CLK_PERIOD"], [14.0, 16.0, 0])
        self.assertEqual(config["_FR_GR_OVERFLOW"], [1, 1, 0])
        self.assertEqual(config["CORE_MARGIN"], [2, 2, 0])        

    def test_read_invalid_config_file(self):
        """
        Tests read_config_file iterface with sweep mode and an invalid JSON file
        """

        with self.assertRaises(ValueError):
            (config, sdc_data, fr_data) = ParamConfigReader.read_config_file("files/bad_autotuner.json", "sweep", "N/A")
        
if __name__ == "__main__":
    unittest.main()
