#!/usr/bin/env python3

import os
import re
import sys
import unittest
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "autotuner"))
from SDCWriter import SDCWriter

class SDCWriterTests(unittest.TestCase):
    """ Tests the SDC writer """

    def test_clk_period_variable(self):
        """ Tests modification of clock definition where we set the clk_period variable """
        
        content = """set clk_name  clk
                     set clk_port_name clk
                     set clk_period 400
                     set clk_io_pct 0.2

                     set clk_port [get_ports $clk_port_name]

                     create_clock -name $clk_name -period $clk_period $clk_port"""
        variables = { "CLK_PERIOD": 200 }
        mod_content = SDCWriter.modify_content(content, variables)
        self.assertEqual(mod_content, content.replace("400", str(variables["CLK_PERIOD"])))

    def test_clk_period_waveform(self):
        """ Tests modification of clock definition where we set the period directly in the create_clock statement """
        
        content = 'create_clock -name "tag_clk" -period 5.2 -waveform {0.0 2.6} [get_ports p_bsg_tag_clk_i]'
        variables = { "CLK_PERIOD": 3.9 }
        mod_content = SDCWriter.modify_content(content, variables)
        content = content.replace("5.2", str(variables["CLK_PERIOD"]))
        content = re.sub(r"-waveform [{}\s0-9\.]+[\s|\n]", "", content)
        self.assertEqual(mod_content, content)

    def test_uncertainty(self):
        """ 
        Tests modification of uncertainty content
        """
        
        content = """set uncertainty 1.0
                     set_clock_uncertainty $uncertainty [all_clocks]"""
        variables = { "UNCERTAINTY": 0.5 }
        mod_content = SDCWriter.modify_content(content, variables)
        self.assertEqual(mod_content, content.replace("1.0", str(variables["UNCERTAINTY"])))

    def test_io_delay(self):
        """ Tests modification of IO delay content """
        
        content = """set io_delay 7.0
                     set_input_delay -clock [get_clocks core_clock] -add_delay -max $io_delay   [all_inputs]
                     set_output_delay -clock [get_clocks core_clock] -add_delay -max $io_delay  [all_outputs]"""
        variables = { "IO_DELAY": 10.0 }
        mod_content = SDCWriter.modify_content(content, variables)
        self.assertEqual(mod_content, content.replace("7.0", str(variables["IO_DELAY"])))

    def test_no_content(self):
        """ Tests error case where no input content is given """
        with self.assertRaises(ValueError):
            mod_content = SDCWriter.modify_content("", {})

    def test_no_uncertainty(self):
        """
        Tests if UNCERTAINTY is in the variable dict, but not in the content

        End result is that we add it to the modified content - not sure this makes sense, but it's a no-op
        """
        
        content = "sample"
        variables = { "UNCERTAINTY": 20 }
        mod_content = SDCWriter.modify_content(content, variables)
        self.assertEqual(mod_content, content + "\nset uncertainty " + str(variables["UNCERTAINTY"]) + "\n")

    def test_no_io_delay(self):
        """ 
        Tests if IO_DELAY is in the variable dict, but not in the content

        End result is that we add it to the modified content - not sure this makes sense, but it's a no-op
        """
        
        content = "sample"
        variables = { "IO_DELAY": 10 }
        mod_content = SDCWriter.modify_content(content, variables)
        self.assertEqual(mod_content, content + "\nset io_delay " + str(variables["IO_DELAY"]) + "\n")

if __name__ == "__main__":
    unittest.main()
    
