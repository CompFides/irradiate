#!/usr/bin/python

# custom ansible filter for atomic red team techniques yaml

# Copyright Compfides  2020  All rights reserved

import os
import re
from ruamel.yaml import YAML
import sys

yaml = YAML()
yaml.explicit_start = True
yaml.default_flow_style = False

def get_self_path():
    return os.path.dirname(os.path.abspath(__file__))

ATOMICS_PATH = os.path.join(get_self_path(), '../files/atomic-red-team/atomics/')
CUSTOM_PATH = os.path.join(get_self_path(), '../files/custom/')
TRANSLATION_PATH = os.path.join(get_self_path(), '../files/translations/translations.yaml')
OUTPUT_PATH = os.path.join(get_self_path(), '../vars/')

TECHNIQUE = "attack_technique"
TESTS = "atomic_tests"
PLATFORMS = "supported_platforms"
ARGUMENTS = "input_arguments"
ARG_KEY = "default"
EXECUTOR = "executor"
COMMAND = "command"
CLEANUP_COMMAND = "cleanup_command"
NAME = "name"

PATTERN = r"\#\{(.+?)\}"

class FilterModule(object):

    def filters(self):

        return {'load_yaml' : self.load_yaml, \
                'load_arguments' : self.load_arguments, \
                'customize_technique' : self.customize_technique, \
                'process_arguments' : self.process_arguments, \
                'translate_command': self.translate_command, \
                'refine_technique' : self.refine_technique, \
                'process_atomic' : self.process_atomic, \
                'process_technique' : self.process_technique}

    def load_yaml(self, file):
    # load yaml as dictionary
    # file - the /path/file to load
    # dictionary - dictionary to hold yaml

        dictionary ={}
        try:
            with open(file, 'r', encoding='utf8') as f:
                # load yaml
                dictionary = yaml.load(f.read())
                f.close()
                return dictionary
        except IOError:
            print("IOError: ", file)

    def load_arguments(self, dictionary, the_key):
    # create dictionary of parameter name:value pairs
    # dictionary - nested dictionary {<input_argument>: {name : value, ... } ... }
    # the_key - key to filter by

        return {name: values[the_key] for name, values in dictionary.items()}

    def customize_technique(self, technique, custom_technique):
    # modify technique with custom_technique settings
    # technique - dictionary describing technique
    # custom_technique - dictionary of custom settings for a technique

        for atomic in technique[TESTS]:
            for custom_atomic in custom_technique[TESTS]:
                if atomic[NAME] == custom_atomic[NAME]:
                    if ARGUMENTS in custom_atomic:
                        for argument in custom_atomic[ARGUMENTS]:
                            atomic[ARGUMENTS][argument][ARG_KEY] = custom_atomic[ARGUMENTS][argument][ARG_KEY]
                    if EXECUTOR in custom_atomic:
                        if COMMAND in custom_atomic[EXECUTOR]:
                            atomic[EXECUTOR][COMMAND] = custom_atomic[EXECUTOR][COMMAND]
                        if CLEANUP_COMMAND in custom_atomic[EXECUTOR]:
                            atomic[EXECUTOR][CLEANUP_COMMAND] = custom_atomic[EXECUTOR][CLEANUP_COMMAND]
        return technique

    def process_arguments(self, field, pattern, dictionary):
    # replace matched fields with arguments
    # field - field searched
    # pattern - regex pattern to search for
    # dictionary - dictionary of replacement values {name : value, ...}

        def replacer(matchobj):
        # <description>
        # matchobj - matched object from re.sub

            if matchobj.group(1) in dictionary:
                val = dictionary[matchobj.group(1)]
            else:
                print("Warning: no match found")
                val = None
            return val
        return re.sub(pattern, replacer, field)

    def translate_command(self, command, os):
    # translate ART command to ansible
    # command - the command to translate
    # os - the operating system

        rosetta_stone = self.load_yaml(TRANSLATION_PATH)
        if os in rosetta_stone[PLATFORMS]:
            if command in rosetta_stone[PLATFORMS][os]:
                command = rosetta_stone[PLATFORMS][os][command]
            else:
                command = ""
        return command

    def refine_technique(self, technique):
    # builds a dictionary of targeted key value pairs
    # technique - technique dictionary to be refined
    # refined - dictionary of targeted key value pairs
    # refined = { <atomic_tests_name> : {supported_platforms : <platform>, command : <command>, \
    #       cleanup_command : <cleanup_command>, ansible_cmd : <ansible_cmd>, \
    #       elevation_required : <elevation_required>} ... }

        refined = {}
        for atomic in technique[TESTS]:
            refined[atomic[NAME]] = {}
            if PLATFORMS in atomic:
                # set supported_platforms to windows or linux
                if 'windows' in atomic[PLATFORMS]:
                    refined[atomic[NAME]][PLATFORMS] = 'windows'
                else:
                    refined[atomic[NAME]][PLATFORMS] = 'linux'
            if EXECUTOR in atomic:
                if COMMAND in atomic[EXECUTOR]:
                    refined[atomic[NAME]][COMMAND] = atomic[EXECUTOR][COMMAND]
                if CLEANUP_COMMAND  in atomic[EXECUTOR]:
                    refined[atomic[NAME]][CLEANUP_COMMAND] = atomic[EXECUTOR][CLEANUP_COMMAND]
            refined[atomic[NAME]]['ansible_cmd'] = self.translate_command(atomic[EXECUTOR][NAME], \
                    refined[atomic[NAME]][PLATFORMS])
            if 'elevation_required' in atomic[EXECUTOR]:
                refined[atomic[NAME]]['elevation_required'] = atomic[EXECUTOR]['elevation_required']
        return refined


    def process_atomic(self, atomic, arguments):
    # arms command and cleanup_command if they exist
    # atomic - atomic to be armed
    # arguments - arguments to arm atomic

        if COMMAND in atomic[EXECUTOR]:
            atomic[EXECUTOR][COMMAND] = self.process_arguments(atomic[EXECUTOR][COMMAND], PATTERN, arguments)
        if CLEANUP_COMMAND in atomic[EXECUTOR]:
            atomic[EXECUTOR][CLEANUP_COMMAND] = self.process_arguments(atomic[EXECUTOR][CLEANUP_COMMAND], PATTERN, arguments)

    def process_technique(self, tech):
    # return yaml description of a technique
    # tech - technique number TXXXX.??.??

        tech_file = ATOMICS_PATH + tech + '/' + tech + '.yaml'
        custom_file = CUSTOM_PATH + tech + '.yaml'
        output_file = OUTPUT_PATH + tech + '.yaml'
        technique = self.load_yaml(tech_file)
        if os.path.isfile(custom_file):
            custom_technique = self.load_yaml(custom_file)
            technique = self.customize_technique(technique, custom_technique)
        for atomic in technique[TESTS]:
            if ARGUMENTS in atomic:
                arguments = self.load_arguments(atomic[ARGUMENTS], ARG_KEY)
                self.process_atomic(atomic, arguments)
        # output to .yaml file and return yaml file name
        try:
            with open(output_file, 'w') as f:
                yaml.dump(self.refine_technique(technique), f)
                f.close()
                return technique[TECHNIQUE] + ".yaml"
        except IOError:
            print("IOError: ", output_file)
        #return str(yaml.dump(self.refine_technique(technique), sys.stdout))[:-4]