from utils.load_template import load_template, load_global, load_heat, load_sec

global_dict = load_global()

def pipeline_build():
    print(global_dict)
    print("pipeline build")