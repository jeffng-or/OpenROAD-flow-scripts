#!/usr/bin/env python3

import re
import argparse
from WriterBase import WriterBase

class FastRouteWriter(WriterBase):
    @staticmethod
    def write_file(orig_content, platform, variables, path, output_file_name): # pragma: no cover
        """
        Create a FastRoute Tcl file with parameters for current tuning
        iteration.
        """

        mod_content = FastRouteWriter.modify_content(orig_content, platform,
                                                     variables)
        return FastRouteWriter._write_file(mod_content, path, output_file_name)
        
    @staticmethod
    def modify_content(orig_content, platform, variables):
        # Handle case where the reference file does not exist
        # (asap7 doesn't have reference)
        if orig_content == "" and platform != "asap7":
            raise ValueError("[ERROR TUN-0021] No FastRoute Tcl reference file provided.")
        layer_cmd = "set_global_routing_layer_adjustment"
        mod_content = orig_content
        for key, value in variables.items():
            if key.startswith("LAYER_ADJUST"):
                layer = key.lstrip("LAYER_ADJUST")
                # If there is no suffix (i.e., layer name) apply adjust to all
                # layers.
                if layer == "":
                    mod_content += "\nset_global_routing_layer_adjustment"
                    mod_content += " $::env(MIN_ROUTING_LAYER)"
                    mod_content += "-$::env(MAX_ROUTING_LAYER)"
                    mod_content += f" {value}"
                elif re.search(f"{layer_cmd}.*{layer}", mod_content):
                    # TODO: Does this work with nangate45 Tcl?
                    mod_content = re.sub(
                        f"({layer_cmd}.*{layer}).*\n(.*)", f"\\1 {value}\n\\2", mod_content
                    )
                else:
                    mod_content += f"\n{layer_cmd} {layer} {value}\n"
            elif key == "GR_SEED":
                mod_content += f"\nset_global_routing_random -seed {value}\n"
        return mod_content
    
    @staticmethod
    def main(): # pragma: no cover
        """ standalone executable interface """
        
        parser = argparse.ArgumentParser(prog="FastRouteWriter.py", description="Performs AutoTuner keyword substitution on FastRoute file")
        parser.add_argument("-i", "--input_file", metavar="file_name",
                            required=True)
        parser.add_argument("-p", "--platform", metavar="platform name",
                            required=True)
        parser.add_argument("-v", "--variable_file", metavar="file_name",
                            required=True)
        parser.add_argument("-O", "--output_path", metavar="output path",
                            default=".")
        parser.add_argument("-o", "--output_file", metavar="output file",
                            required=True)
        args = parser.parse_args()
        FastRouteWriter.write_file(FastRouteWriter.read_content_file(args.input_file),
                                   args.platform,
                                   FastRouteWriter.read_variable_file(args.variable_file),
                                   args.output_path, args.output_file)
        
if __name__ == "__main__": # pragma: no cover
    FastRouteWriter.main()
