#!/usr/bin/env python3

import re
import argparse
from WriterBase import WriterBase

class SDCWriter(WriterBase):
    @staticmethod
    def write_file(orig_content, variables, path, output_file_name): # pragma: no cover
        """
        Create a SDC file with parameters for current tuning iteration.
        """

        mod_content = SDCWriter.modify_content(orig_content, variables)
        return SDCWriter._write_file(mod_content, path, output_file_name)

    @staticmethod
    def modify_content(orig_content, variables):
        """
        Replaces the keywords in the SDC file content and returns the modified
        string

        Currently replaces clock period statement and uncertainty or IO delay
        variables only. If the uncertainty or IO delay variables are not defined
        in the SDC file, but are in the variables dict, they are added to the
        resulting SDC file. Not sure that this makes sense functionally, but
        that's the current behavior.
        """
        
        # Handle case where the reference file does not exist
        if orig_content == "":
            raise ValueError("[ERROR TUN-0020] No SDC reference file provided.")
        mod_content = orig_content
        for key, value in variables.items():
            if key == "CLK_PERIOD":
                if mod_content.find("set clk_period") != -1:
                    # Ex: set clk_period 400
                    mod_content = re.sub(
                        r"set clk_period .*\n(.*)", f"set clk_period {value}\n\\1", mod_content
                    )
                else:
                    # Ex: create_clock -period 400
                    # Removes waveform option
                    mod_content = re.sub(
                        r"-period [0-9\.]+ (.*)", f"-period {value} \\1", mod_content
                    )
                    mod_content = re.sub(r"-waveform [{}\s0-9\.]+[\s|\n]", "", mod_content)
            elif key == "UNCERTAINTY":
                if mod_content.find("set uncertainty") != -1:
                    # Ex: set uncertainty .10
                    mod_content = re.sub(
                        r"set uncertainty .*\n(.*)",
                        f"set uncertainty {value}\n\\1",
                        mod_content,
                    )
                else:
                    mod_content += f"\nset uncertainty {value}\n"
            elif key == "IO_DELAY":
                if mod_content.find("set io_delay") != -1:
                    # Ex: set io_delay .10
                    mod_content = re.sub(
                        r"set io_delay .*\n(.*)", f"set io_delay {value}\n\\1", mod_content
                    )
                else:
                    mod_content += f"\nset io_delay {value}\n"
        return mod_content

    @staticmethod
    def main(): # pragma: no cover
        """ standalone executable interface """
        
        parser = argparse.ArgumentParser(prog="SDCWriter.py", description="Performs AutoTuner keyword substitution on SDC file")
        parser.add_argument("-i", "--input_sdc", metavar="file_name",
                            required=True)
        parser.add_argument("-v", "--variable_file", metavar="file_name",
                            required=True)
        parser.add_argument("-O", "--output_path", metavar="output path",
                            default=".")
        parser.add_argument("-o", "--output_file", metavar="output file",
                            required=True)
        args = parser.parse_args()
        SDCWriter.write_file(SDCWriter.read_content_file(args.input_sdc),
                             SDCWriter.read_variable_file(args.variable_file),
                             args.output_path, args.output_file)
        
if __name__ == "__main__": # pragma: no cover
    SDCWriter.main()
