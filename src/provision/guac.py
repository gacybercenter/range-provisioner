import orchestration.heat as heat
import orchestration.guac as guac
import orchestration.swift as swift
import time
from utils.msg_format import error_msg, info_msg, success_msg, general_msg

def provision(conn, globals, heat_params, sec_params, debug=False):
    name = globals['range_name']