# -*- coding: utf-8 -*-
'''
Updated on December, 2017
@author: Todd Baumeister <tbaumeist@gmail.com>

Add hash value to existing experiments file
'''
import os
import sys
import json
import logging
import argparse

# add parent directory to path, so we can use their classes
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from lib.configuration import Configuration


class Patcher(object):
    ''' Patch hash '''
    def main(self, args):
        ''' Main entry point '''
        output_directory = os.path.abspath(args.d)
        exp_file_path = os.path.join(output_directory, 'experiments.json')
        # load existing experiment configurations
        if not os.path.exists(exp_file_path):
            raise Exception('Unable to file the experiments file')

        with open(exp_file_path, 'r') as e_file:
            experiement_configurations = json.loads(e_file.read())
        total = len(experiement_configurations)
        logging.info('Loaded %s existing experiment configurations', total)

        # patch the hash value into the data structure
        patch_count = 0
        for exp in experiement_configurations:
            if 'hash' not in exp:
                patch_count += 1
                # calculate the hash and add it
                config_file_name = os.path.join(
                    output_directory, exp['config'])
                if not os.path.exists(config_file_name):
                    raise Exception('Unable to find the config file, PANIC!!!')

                with open(config_file_name, 'r') as c_file:
                    config = json.loads(c_file.read())
                exp['hash'] = Configuration.get_hash(config)

        # write the changes back out
        with open(exp_file_path, 'w') as e_file:
            e_file.write(json.dumps(experiement_configurations))

        logging.info('Patched %d experiments', patch_count)


if __name__ == '__main__':
    logging.getLogger().setLevel(logging.INFO)
    PARSER = argparse.ArgumentParser(
        description='Add hash value to existing experiments file.')
    PARSER.add_argument('-d', default='.', type=str, required=True,
                        help='Directory to store output in')
    Patcher().main(PARSER.parse_args())
