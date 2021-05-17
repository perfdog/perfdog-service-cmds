# coding: utf-8

import subprocess
import threading
import time
import grpc

import perfdog_pb2
import perfdog_pb2_grpc
from config import PERFDOG_SERVICE_PATH, PERFDOG_SERVICE_IP, PERFDOG_SERVICE_PORT, PERFDOG_SERVICE_TOKEN
from device_manager import DeviceManager

s_channel = None
s_stub = None
s_device_manager = None


def start_perfdog_service(path):
    def run():
        subprocess.run(path)

    t = threading.Thread(target=run)
    t.setDaemon(True)
    t.start()

    time.sleep(8.0)


def init():
    global s_channel
    global s_stub
    global s_device_manager

    start_perfdog_service(PERFDOG_SERVICE_PATH)
    s_channel = grpc.insecure_channel('%s:%s' % (PERFDOG_SERVICE_IP, PERFDOG_SERVICE_PORT),
                                      options=[('grpc.max_receive_message_length', 100 * 1024 * 1024)]);
    s_stub = perfdog_pb2_grpc.PerfDogServiceStub(s_channel)
    s_stub.loginWithToken(perfdog_pb2.Token(token=PERFDOG_SERVICE_TOKEN))

    s_device_manager = DeviceManager(s_stub)


def de_init():
    global s_channel
    global s_stub
    global s_device_manager

    if s_device_manager is not None:
        s_device_manager = None

    s_stub = None
    s_channel = None


def get_stub():
    return s_stub


def get_device_manager():
    return s_device_manager


def get_apps(device):
    res = s_stub.getAppList(device)
    return res.app


def print_apps(apps):
    for idx, app in enumerate(apps):
        print('apps[%s]: %s->%s' % (idx, app.label, app.packageName))


def get_app_process_list(device, app):
    req = perfdog_pb2.GetAppRunningProcessReq(device=device, app=app)
    res = s_stub.getAppRunningProcess(req)
    return res.processInfo


def get_app_pid_windows_map(device, app):
    req = perfdog_pb2.GetAppWindowsMapReq(device=device, app=app)
    res = s_stub.getAppWindowsMap(req)
    return res.pid2WindowMap


def print_app_pid_windows_map(pid_windows_map):
    for pid, windows_map in pid_windows_map.items():
        print('%s->%s' % (pid, windows_map))


def print_app_process_list(process_list):
    for idx, process in enumerate(process_list):
        print('process[%s]: %s->%s' % (idx, process.name, process.isTop))


def get_sys_process_list(device):
    res = s_stub.getRunningSysProcess(device)
    return res.processInfo


def print_sys_process_list(process_list):
    for idx, process in enumerate(process_list):
        print('process[%s]: %s->%s' % (idx, process.pid, process.name))


def get_device_support_types(device):
    res = s_stub.getAvailableDataType(device)
    return res.type


def print_device_types(types):
    for idx, ty in enumerate(types):
        print('types[%s]: %s' % (idx, ty))


def get_device_types(device):
    res = s_stub.getPerfDataType(device)
    return res.type


def enable_device_type(device, ty):
    req = perfdog_pb2.EnablePerfDataTypeReq(device=device, type=ty)
    s_stub.enablePerfDataType(req)


def disable_device_type(device, ty):
    req = perfdog_pb2.DisablePerfDataTypeReq(device=device, type=ty)
    s_stub.disablePerfDataType(req)


def set_screenshot_interval(device, seconds):
    req = perfdog_pb2.ScreenShotInterval(device=device, second=seconds)
    s_stub.setScreenShotInterval(req)


def start_app_test(device, app):
    req = perfdog_pb2.StartTestAppReq(device=device, app=app)
    s_stub.startTestApp(req)


def start_app_process_test(device, app, process, is_hide_float_window, sub_window):
    req = perfdog_pb2.StartTestAppReq(
        device=device,
        app=app, subProcess=process.name,
        hideFloatingWindow=is_hide_float_window,
        subWindow=sub_window)
    s_stub.startTestApp(req)


def start_sys_process_test(device, process, is_hide_float_window):
    req = perfdog_pb2.StartTestSysProcessReq(
        device=device,
        sysProcessInfo=process,
        hideFloatingWindow=is_hide_float_window)
    s_stub.startTestSysProcess(req)
