# coding: utf-8

import sys
import threading

import perfdog_pb2
from cmd_base import Command, Quit, Menu
from config import PERFDOG_SERVICE_OUTPUT_DIRECTORY
from stub import set_screenshot_interval, get_app_process_list, print_app_process_list, \
    start_app_process_test, print_sys_process_list, get_sys_process_list, start_sys_process_test, get_apps, \
    print_apps, start_app_test, get_device_support_types, print_device_types, disable_device_type, enable_device_type, \
    get_device_types, get_device_manager, get_stub, get_app_pid_windows_map, \
    print_app_pid_windows_map


class MonitorDevice(Command):
    def execute(self):
        class Listener:
            @staticmethod
            def on_add_device(device):
                print('Add Device:')
                print(device)

            @staticmethod
            def on_remove_device(device):
                print('Remove Device:')
                print(device)

        get_device_manager().set_device_listener(Listener())
        input('')
        get_device_manager().set_device_listener(None)

        return Quit()


class PrintDevices(Command):
    def execute(self):
        get_device_manager().print_devices()
        return Quit()


class DeviceBase(Command):
    def execute(self):
        get_device_manager().print_devices()
        idx = int(input('请选择相应的设备：'))
        device = get_device_manager().get_device(idx)
        return self.do_execute(device)

    def do_execute(self, device):
        raise NotImplementedError()


class GetDeviceStatus(DeviceBase):
    def do_execute(self, device):
        print(get_stub().getDeviceStatus(device))
        return Quit()


class InitDevice(DeviceBase):
    def do_execute(self, device):
        res = get_stub().getDeviceStatus(device)
        if res.isTesting:
            return True, DeviceContext(device)

        get_stub().initDevice(device)
        return True, DeviceContext(device)


class SetGlobalDataUploadServer(Command):
    def execute(self):
        server_url = input('请输入第三方数据上传服务地址：')
        print('0. json')
        print('1. pb')
        server_format = int(input('请选择要上传的格式：'))
        req = perfdog_pb2.SetDataUploadServerReq(serverUrl=server_url, dataUploadFormat=server_format)
        get_stub().setGlobalDataUploadServer(req)

        return Quit()


class ClearGlobalDataUploadServer(Command):
    def execute(self):
        req = perfdog_pb2.SetDataUploadServerReq(serverUrl='')
        get_stub().setGlobalDataUploadServer(req)

        return Quit()


class SetScreenShotInterval(DeviceBase):
    def do_execute(self, device):
        seconds = int(input('请输入截屏时间间隔：'))
        set_screenshot_interval(device, seconds)
        return Quit()


class SaveTestData(DeviceBase):
    def do_execute(self, device):
        begin_time = int(input('请输入保存数据开始时间点:'))
        end_time = int(input('请输入保存数据结束时间点:'))
        case_name = input('请输入case名称:')
        is_upload = True if input('是否上传到云服务(y/n):') in 'yY' else False
        is_export = True if input('是否保存到本地(y/n):') in 'yY' else False
        print('0. excel')
        print('1. json')
        print('2. pb')
        output_format = int(input('请选择导出格式：'))
        req = perfdog_pb2.SaveDataReq(
            device=device,
            beginTime=begin_time,
            endTime=end_time,
            caseName=case_name,
            uploadToServer=is_upload,
            exportToFile=is_export,
            outputDirectory=PERFDOG_SERVICE_OUTPUT_DIRECTORY,
            dataExportFormat=output_format,
        )
        print(get_stub().saveData(req))

        return Quit()


class GetDeviceCacheData(DeviceBase):
    def do_execute(self, device):
        req = perfdog_pb2.GetDeviceCacheDataReq(device=device)
        stream = get_stub().getDeviceCacheData(req)
        t = threading.Thread(target=self.run, args=(stream,))
        t.start()
        input('')
        stream.cancel()
        t.join()

        return Quit()

    @staticmethod
    def run(stream):
        try:
            for d in stream:
                print(d)
        except Exception as e:
            print(e)


class GetDeviceCacheDataPacked(DeviceBase):
    def do_execute(self, device):
        print('0. json')
        print('1. pb')
        data_format = int(input('请选择要拉取设备缓存数据格式:'))
        req = perfdog_pb2.GetDeviceCacheDataPackedReq(device=device, dataFormat=data_format)
        stream = get_stub().getDeviceCacheDataPacked(req)
        t = threading.Thread(target=self.run, args=(stream,))
        t.start()
        input('')
        stream.cancel()
        t.join()

        return Quit()

    @staticmethod
    def run(stream):
        try:
            for d in stream:
                print(d)
        except Exception as e:
            print(e)


class CreateTask(Command):
    def execute(self):
        task_name = input('请输入任务名:')
        req = perfdog_pb2.CreateTaskReq(taskName=task_name)
        print(get_stub().createTask(req))

        return Quit()


class ArchiveCaseToTask(Command):
    def execute(self):
        case_id = input('请输入caseID：')
        task_id = input('请输入任务ID：')
        req = perfdog_pb2.ArchiveCaseToTaskReq(caseId=case_id, taskId=task_id)
        get_stub().archiveCaseToTask(req)

        return Quit()


class ShareCase(Command):
    def execute(self):
        case_id = input('请输入caseID：')
        expire_time = int(input('请输入失效时间: '))
        req = perfdog_pb2.ShareCaseReq(caseId=case_id, expireTime=expire_time)
        print(get_stub().shareCase(req))

        return Quit()


class KillServer(Command):
    def execute(self):
        req = perfdog_pb2.Empty()
        print(get_stub().killServer(req))
        sys.exit(0)

        return Quit()


class DeviceContext(Menu):
    def __init__(self, device):
        super(DeviceContext, self).__init__([
            GetDeviceInfo('获取设备信息', device),
            GetDeviceAppList('获取App列表', device),
            GetDeviceAppProcessList('获取App进程列表', device),
            GetDeviceAppWindowsMap('获取App进程对应的Activity和SurfaceView', device),
            GetDeviceSysProcessList('获取系统进程列表', device),
            UpdateAppInfo('更新App信息', device),
            GetDeviceSupportTypes('获取设备支持的测试类型', device),
            GetDeviceTypes('获取设备当前打开的测试类型', device),
            EnableDeviceType('启用设备测试类型', device),
            DisableDeviceType('禁用设备测试类型', device),
            StartTest('开始测试', device),
            StopTest('结束测试', device),
        ])


class GetDeviceInfo(Command):
    def __init__(self, desc, device):
        super(GetDeviceInfo, self).__init__(desc)
        self.device = device

    def execute(self):
        print(get_stub().getDeviceInfo(self.device))
        return Quit()


class GetDeviceAppList(Command):
    def __init__(self, desc, device):
        super(GetDeviceAppList, self).__init__(desc)
        self.device = device

    def execute(self):
        apps = get_apps(self.device)
        print_apps(apps)
        return Quit()


class GetDeviceAppProcessList(Command):
    def __init__(self, desc, device):
        super(GetDeviceAppProcessList, self).__init__(desc)
        self.device = device

    def execute(self):
        apps = get_apps(self.device)
        print_apps(apps)
        idx = int(input('请选择要获取进程列表的App：'))
        process_list = get_app_process_list(self.device, apps[idx])
        print_app_process_list(process_list)
        return Quit()


class GetDeviceAppWindowsMap(Command):
    def __init__(self, desc, device):
        super(GetDeviceAppWindowsMap, self).__init__(desc)
        self.device = device

    def execute(self):
        apps = get_apps(self.device)
        print_apps(apps)
        idx = int(input('请选择要获取信息的App：'))
        pid_windows_map = get_app_pid_windows_map(self.device, apps[idx])
        print_app_pid_windows_map(pid_windows_map)
        return Quit()


class GetDeviceSysProcessList(Command):
    def __init__(self, desc, device):
        super(GetDeviceSysProcessList, self).__init__(desc)
        self.device = device

    def execute(self):
        process_list = get_sys_process_list(self.device)
        print_sys_process_list(process_list)
        return Quit()


class UpdateAppInfo(Command):
    def __init__(self, desc, device):
        super(UpdateAppInfo, self).__init__(desc)
        self.device = device

    def execute(self):
        apps = get_apps(self.device)
        print_apps(apps)
        idx = int(input('请选择要测试的App：'))
        app = apps[idx]
        req = perfdog_pb2.UpdateAppInfoReq(device=self.device, app=app)
        print(get_stub().updateAppInfo(req))

        return Quit()


class GetDeviceSupportTypes(Command):
    def __init__(self, desc, device):
        super(GetDeviceSupportTypes, self).__init__(desc)
        self.device = device

    def execute(self):
        types = get_device_support_types(self.device)
        print_device_types(types)
        return Quit()


class GetDeviceTypes(Command):
    def __init__(self, desc, device):
        super(GetDeviceTypes, self).__init__(desc)
        self.device = device

    def execute(self):
        types = get_device_types(self.device)
        print_device_types(types)
        return Quit()


class EnableDeviceType(Command):
    def __init__(self, desc, device):
        super(EnableDeviceType, self).__init__(desc)
        self.device = device

    def execute(self):
        types = get_device_support_types(self.device)
        print_device_types(types)
        idx = int(input('请选择要启用的类型：'))
        enable_device_type(self.device, types[idx])
        return Quit()


class DisableDeviceType(Command):
    def __init__(self, desc, device):
        super(DisableDeviceType, self).__init__(desc)
        self.device = device

    def execute(self):
        types = get_device_support_types(self.device)
        print_device_types(types)
        idx = int(input('请选择要关闭的类型：'))
        disable_device_type(self.device, types[idx])
        return Quit()


class StartTest(Command):
    def __init__(self, desc, device):
        super(StartTest, self).__init__(desc)
        self.device = device

    def execute(self):
        res = get_stub().getDeviceStatus(self.device)
        if res.isTesting:
            return True, TestContext(self.device)

        self.print_usage()
        idx = int(input('选择要测试的类型：'))

        if idx == 0:
            self.test_app()
        elif idx == 1:
            self.test_app_process()
        elif idx == 2:
            self.test_sys_process()
        else:
            return Quit()

        return True, TestContext(self.device)

    @staticmethod
    def print_usage():
        print('0. app')
        print('1. app process')
        print('2. sys process')

    def test_app(self):
        apps = get_apps(self.device)
        print_apps(apps)
        idx = int(input('请选择要测试的App：'))
        app = apps[idx]
        start_app_test(self.device, app)

    def test_app_process(self):
        apps = get_apps(self.device)
        print_apps(apps)
        idx = int(input('请选择要测试的App：'))
        app = apps[idx]

        process_list = get_app_process_list(self.device, app)
        print_app_process_list(process_list)
        idx = int(input('请选择要测试App进程：'))
        process = process_list[idx]

        is_hide_float_window = True if input('是否隐藏浮窗(y/n):') in 'yY' else False
        is_test_sub_window = True if input('是否测试子窗口(y/n):') in 'yY' else False
        if is_test_sub_window:
            sub_list = get_app_pid_windows_map(self.device, app)
            print_app_pid_windows_map(sub_list)
            sub_window = input('请输入要获取的子窗口名字：')
        else:
            sub_window = None

        start_app_process_test(self.device, app, process, is_hide_float_window, sub_window)

    def test_sys_process(self):
        process_list = get_sys_process_list(self.device)
        print_sys_process_list(process_list)
        idx = int(input('请选择要测试系统进程：'))
        process = process_list[idx]
        is_hide_float_window = True if input('是否隐藏浮窗(y/n):') in 'yY' else False

        start_sys_process_test(self.device, process, is_hide_float_window)


class StopTest(Command):
    def __init__(self, desc, device):
        super(StopTest, self).__init__(desc)
        self.device = device

    def execute(self):
        req = perfdog_pb2.StopTestReq(device=self.device)
        get_stub().stopTest(req)

        return Quit()


class TestContext(Menu):
    def __init__(self, device):
        super(TestContext, self).__init__([
            OpenPerfDataStream('获取当前测试设备的实时测试数据流(按任意键结束)', device),
            SetLabel('设置标签', device),
            UpdateLabel('更新标签', device),
            AddNote('添加标注', device),
            RemoteNote('删除标注', device),
        ])


class OpenPerfDataStream(Command):
    def __init__(self, desc, device):
        super(OpenPerfDataStream, self).__init__(desc)
        self.device = device

    def execute(self):
        req = perfdog_pb2.OpenPerfDataStreamReq(device=self.device)
        stream = get_stub().openPerfDataStream(req)
        t = threading.Thread(target=self.run, args=(stream,))
        t.start()
        input('')
        stream.cancel()
        t.join()

        return Quit()

    @staticmethod
    def run(stream):
        try:
            for data in stream:
                print(data)
        except Exception as e:
            print(e)


class SetLabel(Command):
    def __init__(self, desc, device):
        super(SetLabel, self).__init__(desc)
        self.device = device

    def execute(self):
        label_name = input('请输入标签名字：')
        req = perfdog_pb2.SetLabelReq(device=self.device, label=label_name)
        print(get_stub().setLabel(req))

        return Quit()


class UpdateLabel(Command):
    def __init__(self, desc, device):
        super(UpdateLabel, self).__init__(desc)
        self.device = device

    def execute(self):
        label_time = int(input('请输入标签时间戳：'))
        label_name = input('请输入标签名字：')
        req = perfdog_pb2.UpdateLabelReq(device=self.device, time=label_time, label=label_name)
        get_stub().updateLabel(req)

        return Quit()


class AddNote(Command):
    def __init__(self, desc, device):
        super(AddNote, self).__init__(desc)
        self.device = device

    def execute(self):
        note_time = int(input('请输入标注时间戳：'))
        note_name = input('请输入标注名字：')
        req = perfdog_pb2.AddNoteReq(device=self.device, time=note_time, note=note_name)
        get_stub().addNote(req)

        return Quit()


class RemoteNote(Command):
    def __init__(self, desc, device):
        super(RemoteNote, self).__init__(desc)
        self.device = device

    def execute(self):
        note_time = int(input('请输入标注时间戳：'))
        req = perfdog_pb2.RemoveNoteReq(device=self.device, time=note_time)
        get_stub().removeNote(req)

        return Quit()


def get_top_menus():
    return [
        MonitorDevice('监控设备连接断开情况'),
        PrintDevices('打印当前连接所有设备'),
        GetDeviceStatus('获取设备状态'),
        InitDevice('初始化设备'),
        SetGlobalDataUploadServer('配置第三方数据存储服务'),
        ClearGlobalDataUploadServer('清除第三方数据存储服务配置'),
        SetScreenShotInterval('配置设备截屏时间间隔'),
        SaveTestData('保存数据'),
        GetDeviceCacheData('单条拉取设备缓存数据(按任意键结束)'),
        GetDeviceCacheDataPacked('批量拉取设备缓存数据(按任意键结束)'),
        CreateTask('创建任务'),
        ArchiveCaseToTask('归档Case到任务'),
        ShareCase('分享Case'),
        KillServer('killServer'),
    ]
