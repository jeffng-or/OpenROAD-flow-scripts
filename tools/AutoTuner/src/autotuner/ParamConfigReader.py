#!/usr/bin/env python3

import os
import json
import numpy as np
import argparse

import ray
from ray import tune

class ParamConfigReader:
    @staticmethod
    def read_config_file(file_name, mode, algorithm):
        """
        Please consider inclusive, exclusive
        Most type uses [min, max)
        But, Quantization makes the upper bound inclusive.
        e.g., qrandint and qlograndint uses [min, max]
        step value is used for quantized type (e.g., quniform). Otherwise, write 0.
        When min==max, it means the constant value
        """
    
        # Check file exists and whether it is a valid JSON file.
        assert os.path.isfile(file_name), f"File {file_name} not found."
        try:
            with open(file_name) as file:
                data = json.load(file)
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON file: {file_name}")
        return ParamConfigReader.read_config(data, mode, algorithm,
                                             os.path.dirname(file_name))

    @staticmethod
    def read_config(data, mode, algorithm, config_file_dir_name):
        """
        TODO: don't think that the two cases where we overwrite data will ever
        occur, since the data is a dictionary without duplicate keys. Marking
        that code as nocover for now
        """
        
        sdc_file = ""
        fr_file = ""
        if mode == "tune" and algorithm == "ax":
            config = list()
        else:
            config = dict()
        for key, value in data.items():
            if key == "best_result":
                continue
            if key == "_SDC_FILE_PATH" and value != "":
                if sdc_file != "": # pragma: no cover
                    print("[WARNING TUN-0004] Overwriting SDC base file.")
                sdc_file = ParamConfigReader.read_content(f"{config_file_dir_name}/{value}")
                continue
            if key == "_FR_FILE_PATH" and value != "":
                if fr_file != "": # pragma: no cover
                    print("[WARNING TUN-0005] Overwriting FastRoute base file.")
                fr_file = ParamConfigReader.read_content(f"{config_file_dir_name}/{value}")
                continue
            if not isinstance(value, dict):
                # To take care of empty values like _FR_FILE_PATH
                if mode == "tune" and algorithm == "ax":
                    param_dict = ParamConfigReader.read_tune_ax(key, value)
                    if param_dict:
                        config.append(param_dict)
                elif mode == "tune" and algorithm == "pbt":
                    param_dict = ParamConfigReader.read_tune_pbt(key, value)
                    if param_dict:
                        config[key] = param_dict
                else:
                    config[key] = value
            elif mode == "sweep":
                config[key] = ParamConfigReader.read_sweep(value)
            elif mode == "tune" and algorithm == "ax":
                config.append(ParamConfigReader.read_tune_ax(key, value))
            elif mode == "tune" and algorithm == "pbt":
                config[key] = ParamConfigReader.read_tune_pbt(key, value)
            elif mode == "tune":
                config[key] = ParamConfigReader.read_tune(value)
        if mode == "tune":
            config = ParamConfigReader.apply_condition(config, data, algorithm)
        return config, sdc_file, fr_file

    @staticmethod
    def read_content(path):
        """ 
        Reads file content into a string and returns it

        if file path does not exist, return empty string
        """
        print(os.path.abspath(path))
        if not os.path.isfile(os.path.abspath(path)):
            return ""
        with open(os.path.abspath(path), "r") as file:
            ret = file.read()
        return ret
    
    @staticmethod
    def read_sweep(this):
        """
        Converts parameter into array of three elements [min, max, step]

        TODO: handle case where we want to sweep through input data that doesn't
        have a step (e.g. DIEAREA or GRT parameters)
        """
        return [*this["minmax"], this["step"]]
    
    @staticmethod
    def apply_condition(config, data, algorithm):
        # TODO: tune.sample_from only supports random search algorithm.
        # To make conditional parameter for the other algorithms, different
        # algorithms should take different methods (will be added)
        if algorithm != "random" or "CELL_PAD_IN_SITES_DETAIL_PLACEMENT" not in data:
            return config
        dp_pad_min = data["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"]["minmax"][0]
        dp_pad_step = data["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"]["step"]
        if dp_pad_step == 1:
            config["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"] = tune.sample_from(
                lambda spec: np.random.randint(
                    dp_pad_min, spec.config.CELL_PAD_IN_SITES_GLOBAL_PLACEMENT + 1
                )
            )
        if dp_pad_step > 1:
            config["CELL_PAD_IN_SITES_DETAIL_PLACEMENT"] = tune.sample_from(
                lambda spec: random.randrange(
                    dp_pad_min,
                    spec.config.CELL_PAD_IN_SITES_GLOBAL_PLACEMENT + 1,
                    dp_pad_step,
                )
            )
        return config

    @staticmethod
    def read_tune(this):
        min_, max_ = this["minmax"]
        if min_ == max_:
            # Returning a choice of a single element allow pbt algorithm to
            # work. pbt does not accept single values as tunable.
            return tune.choice([min_, max_])
        if this["type"] == "int":
            if this["step"] == 1:
                return tune.randint(min_, max_)
            return tune.choice(np.ndarray.tolist(np.arange(min_, max_, this["step"])))
        if this["type"] == "float":
            if this["step"] == 0:
                return tune.uniform(min_, max_)
            return tune.choice(np.ndarray.tolist(np.arange(min_, max_, this["step"])))
        return None

    @staticmethod
    def read_tune_ax(name, this):
        """
        Ax format: https://ax.dev/versions/0.3.7/api/service.html
        """
        dict_ = dict(name=name)
        if "minmax" not in this:
            return None
        min_, max_ = this["minmax"]
        if min_ == max_:
            dict_["type"] = "fixed"
            dict_["value"] = min_
        elif this["type"] == "int":
            if this["step"] == 1:
                dict_["type"] = "range"
                dict_["bounds"] = [min_, max_]
                dict_["value_type"] = "int"
            else:
                # TODO: this is an error. randint only supports two args
                dict_["type"] = "choice"
                dict_["values"] = tune.randint(min_, max_, this["step"])
                dict_["value_type"] = "int"
        elif this["type"] == "float":
            if this["step"] == 1:
                dict_["type"] = "choice"
                dict_["values"] = tune.choice(
                    np.ndarray.tolist(np.arange(min_, max_, this["step"]))
                )
                dict_["value_type"] = "float"
            else:
                dict_["type"] = "range"
                dict_["bounds"] = [min_, max_]
                dict_["value_type"] = "float"
        return dict_

    @staticmethod
    def read_tune_pbt(name, this):
        """
        PBT format: https://docs.ray.io/en/releases-2.9.3/tune/examples/pbt_guide.html
        Note that PBT does not support step values.
        """
        if "minmax" not in this:
            return None
        min_, max_ = this["minmax"]
        if min_ == max_:
            return ray.tune.choice([min_, max_])
        if this["type"] == "int":
            return ray.tune.randint(min_, max_)
        if this["type"] == "float":
            return ray.tune.uniform(min_, max_)

    @staticmethod
    def main(): # pragma: no cover
        """ standalone executable interface """
        
        parser = argparse.ArgumentParser(prog="ParamConfigReader.py", description="Reads AutoTuner parameter space definition file and converts it for use with Ray")
        parser.add_argument("-i", "--input_file", metavar="file_name",
                            required=True)
        parser.add_argument("-m", "--mode", metavar="mode", choices=["sweep", "tune"], help="Mode type: sweep or tune",
                            required=True)
        parser.add_argument("-a", "--algorithm", metavar="algorithm",
                            default="hyperopt", choices=["ax", "pbt", "hyperopt", "optuna", "random"], help="Tune algorithm choice: ax, pbt, hyperopt, optuna, random")
        args = parser.parse_args()
        (config, sdc_content, fastroute_content) = ParamConfigReader.read_config_file(args.input_file, args.mode, args.algorithm)
        print("Config:")
        print(config)
        print("\nSDC Content:")
        print(sdc_content)
        print("\nFastRoute Content:")
        print(fastroute_content)
    
if __name__ == "__main__": # pragma: no cover
    ParamConfigReader.main()
