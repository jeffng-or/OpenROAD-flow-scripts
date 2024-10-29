#!/usr/bin/env python3

import os
import re
import sys
import unittest
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "autotuner"))
from FastRouteWriter import FastRouteWriter

class FastRouteWriterTests(unittest.TestCase):
    """ 
    Tests the FastRoute writer

    TODO: add following tests
        pre-existing set_global_routing_layer_adjustment metal2-metal3 with LAYER_ADJUST - old should be removed
        pre-existing set_global_routing_layer_adjustment $::env(MIN_ROUTING_LAYER)-$::env(MAX_ROUTING_LAYER) with LAYER_ADJUST - new value should replace old
        pre-existing set_global_routing_layer_adjustment metal2-metal3 with LAYER_ADJUSTmetal3 - old should be split into metal2 and metal3 with metal3 getting new value
        pre-existing set_global_routing_layer_adjustment * with ADJUST_LAYER - new should replace old
        pre-existing set_global_routing_layer_adjustment * with ADJUST_LAYERmetal1 - * should be split into metal2-$::env(MAX_ROUTING_LAYER) and metal1 should get new value
        pre-existing set_global_routing_layer_adjustment with ADJUST_LAYER* - replace old with new
    """

    def test_layer_adjust_all_layers(self):
        """
        Tests modification of layer adjust when layer is not defined in key
        """
        
        content = "bogus"
        variables = { "LAYER_ADJUST": 0.25 }
        mod_content = FastRouteWriter.modify_content(content, "", variables)
        self.assertEqual(mod_content, content + "\nset_global_routing_layer_adjustment $::env(MIN_ROUTING_LAYER)-$::env(MAX_ROUTING_LAYER) " + str(variables["LAYER_ADJUST"]))

    def test_layer_adjust_existing_layer(self):
        """ 
        Tests modification of layer adjust when one layer is defined and layer
        already defined in content
        """
        
        layer_name = "metal1"
        content = "set_global_routing_layer_adjustment " + layer_name + " 0.5\n"
        variables = { "LAYER_ADJUST" + layer_name: 0.25 }
        mod_content = FastRouteWriter.modify_content(content, "", variables)
        self.assertEqual(mod_content, content.replace("0.5", str(variables["LAYER_ADJUST" + layer_name])))

    def test_layer_adjust_non_existing_layer(self):
        """ 
        Tests modification of layer adjust when one layer is defined and it 
        doesn't exist in the content
        """
        
        content = "bogus"
        layer_name = "metal1"
        variables = { "LAYER_ADJUST" + layer_name: 0.25 }
        mod_content = FastRouteWriter.modify_content(content, "", variables)
        self.assertEqual(mod_content, content + "\nset_global_routing_layer_adjustment " + layer_name + " " + str(variables["LAYER_ADJUST" + layer_name]) + "\n")

    def test_layer_adjust_multiple_existing_layers(self):
        """ 
        Tests modification of layer adjust when multiple layers are defined and
        exist in the content
        """

        content = ""
        layer_names = [ "metal1", "metal2" ]
        for layer_name in layer_names:
            content += "set_global_routing_layer_adjustment " + layer_name + " 0.5\n"
        variable_keys = ["LAYER_ADJUST" + layer_name for layer_name in layer_names]
        variables = dict.fromkeys(variable_keys, 0.25)
        mod_content = FastRouteWriter.modify_content(content, "", variables)
        self.assertEqual(mod_content, content.replace("0.5", "0.25"))

    def test_layer_adjust_multiple_non_existing_layers(self):
        """ 
        Tests modification of layer adjust when multiple layers are defined and
        they don't exist in the content
        """
        
        content = "bogus"
        layer_names = [ "metal1", "metal2" ]
        variable_keys = ["LAYER_ADJUST" + layer_name for layer_name in layer_names]
        variables = dict.fromkeys(variable_keys, 0.25)
        mod_content = FastRouteWriter.modify_content(content, "", variables)
        for layer_name in layer_names:
            content += "\nset_global_routing_layer_adjustment " + layer_name + " " + str(variables["LAYER_ADJUST" + layer_name]) + "\n"
        self.assertEqual(mod_content, content)

    def test_gr_seed(self):
        """ 
        Tests modification of global route seed
        """
        
        content = "bogus"
        variables = { "GR_SEED": 1234 }
        mod_content = FastRouteWriter.modify_content(content, "", variables)
        self.assertEqual(mod_content, content + "\nset_global_routing_random -seed " + str(variables["GR_SEED"]) + "\n")

    def test_no_content(self):
        """ Tests error case where no input content is given """
        with self.assertRaises(ValueError):
            mod_content = FastRouteWriter.modify_content("", "", {})

    def test_no_content_asap7(self):
        """
        Tests error case where no input content is given and platform is asap7
        """

        content = ""
        mod_content = FastRouteWriter.modify_content(content, "asap7", {})
        self.assertEqual(mod_content, content)

    def test_no_content_non_asap7(self):
        """
        Tests error case where no input content is given and platform isn't
        asap7
        """
        
        with self.assertRaises(ValueError):
            mod_content = FastRouteWriter.modify_content("", "nangate45", {})
            
if __name__ == "__main__":
    unittest.main()
    
