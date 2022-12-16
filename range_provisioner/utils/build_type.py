from utils.load_template import load_template, load_global, load_heat, load_sec
from object_store.swift import create_container


def pipeline_provision(args):
    print(args)
    create_container()


def cli_provision(args):
    print(args)


def provision(args):
    if args.pipeline is True:
        print("true")
        pipeline_provision(args)