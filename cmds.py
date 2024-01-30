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

        event_stream = get_device_manager().start_monitor(Listener())
        input('')
        get_device_manager().stop_monitor(event_stream)

        return Quit()


class PrintDevices(Command):
    def execute(self):
        get_device_manager().print_devices()
        return Quit()


class DeviceBase(Command):
    def execute(self):
        device = get_device_manager().select_device()
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
        server_url = input('Please enter the third-party data upload service address:')
        print('0. json')
        print('1. pb')
        server_format = int(input('Please select the format to upload:'))
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
        seconds = int(input('Please enter the screenshot interval:'))
        set_screenshot_interval(device, seconds)
        return Quit()


class EnableInstallApk(Command):
    def execute(self):
        preferences = perfdog_pb2.Preferences(doNotInstallPerfDogApp=False)
        req = perfdog_pb2.SetPreferencesReq(preferences=preferences)
        get_stub().setPreferences(req)
        return Quit()


class DisableInstallApk(Command):
    def execute(self):
        preferences = perfdog_pb2.Preferences(doNotInstallPerfDogApp=True)
        req = perfdog_pb2.SetPreferencesReq(preferences=preferences)
        get_stub().setPreferences(req)
        return Quit()


class SaveTestData(DeviceBase):
    def do_execute(self, device):
        begin_time = int(input('Please enter the start time point for saving data:'))
        end_time = int(input('Please enter the end time of saving data:'))
        case_name = input('Please enter case name:')
        is_upload = True if input('Whether to upload to cloud service (y/n):') in 'yY' else False
        is_export = True if input('Whether to save locally (y/n):') in 'yY' else False
        print('0. excel')
        print('1. json')
        print('2. pb')
        output_format = int(input('Please select the export format:'))
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
        data_format = int(input('Please select the device cache data format to be pulled:'))
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
        task_name = input('Please enter the task name:')
        req = perfdog_pb2.CreateTaskReq(taskName=task_name)
        print(get_stub().createTask(req))

        return Quit()


class ArchiveCaseToTask(Command):
    def execute(self):
        case_id = input('Please enter case ID:')
        task_id = input('Please enter the task ID:')
        req = perfdog_pb2.ArchiveCaseToTaskReq(caseId=case_id, taskId=task_id)
        get_stub().archiveCaseToTask(req)

        return Quit()


class ShareCase(Command):
    def execute(self):
        case_id = input('Please enter case ID:')
        expire_time = int(input('Please enter expiry time:'))
        non_password = True if input('Whether to cancel sharing password (y/n):') in 'yY' else False
        req = perfdog_pb2.ShareCaseReq(caseId=case_id, expireTime=expire_time, nonPassword=non_password)
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
            GetDeviceInfo('Get device information', device),
            GetDeviceAppList('Get App list', device),
            GetDeviceAppProcessList('Get App process list', device),
            GetDeviceAppWindowsMap('Get the Activity and SurfaceView corresponding to the App process', device),
            GetDeviceSysProcessList('Get system process list', device),
            UpdateAppInfo('Update App information', device),
            GetDeviceSupportTypes('Get the test types supported by the device', device),
            GetDeviceTypes('Get the test type currently opened by the device', device),
            EnableDeviceType('Enable device test type', device),
            DisableDeviceType('Disable device test type', device),
            StartTest('Start testing', device),
            StopTest('End test', device),
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
        idx = int(input('Please select the App you want to get the process list:'))
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
        idx = int(input('Please select the App you want to obtain information from:'))
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
        idx = int(input('Please select the App you want to test:'))
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
        idx = int(input('Please select the type to enable:'))
        enable_device_type(self.device, types[idx])
        return Quit()


class DisableDeviceType(Command):
    def __init__(self, desc, device):
        super(DisableDeviceType, self).__init__(desc)
        self.device = device

    def execute(self):
        types = get_device_support_types(self.device)
        print_device_types(types)
        idx = int(input('Please select the type of disable:'))
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
        idx = int(input('Choose the type to test:'))

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
        idx = int(input('Please select the App you want to test:'))
        app = apps[idx]
        start_app_test(self.device, app)

    def test_app_process(self):
        apps = get_apps(self.device)
        print_apps(apps)
        idx = int(input('Please select the App you want to test:'))
        app = apps[idx]

        process_list = get_app_process_list(self.device, app)
        print_app_process_list(process_list)
        idx = int(input('Please select the App process to test:'))
        process = process_list[idx]

        is_hide_float_window = True if input('Whether to hide the floating window (y/n):') in 'yY' else False
        is_test_sub_window = True if input('Whether to test the sub-window (y/n):') in 'yY' else False
        if is_test_sub_window:
            sub_list = get_app_pid_windows_map(self.device, app)
            print_app_pid_windows_map(sub_list)
            sub_window = input('Please enter the name of the subwindow you want to get:')
        else:
            sub_window = None

        start_app_process_test(self.device, app, process, is_hide_float_window, sub_window)

    def test_sys_process(self):
        process_list = get_sys_process_list(self.device)
        print_sys_process_list(process_list)
        idx = int(input('Please select a system process to test:'))
        process = process_list[idx]
        is_hide_float_window = True if input('Whether to hide the floating window (y/n):') in 'yY' else False

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
            OpenPerfDataStream('Get the real-time test data stream of the current test device (press any key to end)', device),
            SetLabel('Set label', device),
            UpdateLabel('Update label', device),
            AddNote('Add tag', device),
            RemoteNote('Delete tag', device),
            GetRenderResolution('Get rendering resolution (for Android)', device),
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
        label_name = input('Please enter the label name:')
        req = perfdog_pb2.SetLabelReq(device=self.device, label=label_name)
        print(get_stub().setLabel(req))

        return Quit()


class UpdateLabel(Command):
    def __init__(self, desc, device):
        super(UpdateLabel, self).__init__(desc)
        self.device = device

    def execute(self):
        label_time = int(input('Please enter label timestamp:'))
        label_name = input('Please enter the label name:')
        req = perfdog_pb2.UpdateLabelReq(device=self.device, time=label_time, label=label_name)
        get_stub().updateLabel(req)

        return Quit()


class AddNote(Command):
    def __init__(self, desc, device):
        super(AddNote, self).__init__(desc)
        self.device = device

    def execute(self):
        note_time = int(input('Please enter tag timestamp:'))
        note_name = input('Please enter the tag name:')
        req = perfdog_pb2.AddNoteReq(device=self.device, time=note_time, note=note_name)
        get_stub().addNote(req)

        return Quit()


class RemoteNote(Command):
    def __init__(self, desc, device):
        super(RemoteNote, self).__init__(desc)
        self.device = device

    def execute(self):
        note_time = int(input('Please enter tag timestamp:'))
        req = perfdog_pb2.RemoveNoteReq(device=self.device, time=note_time)
        get_stub().removeNote(req)

        return Quit()


class GetRenderResolution(Command):
    def __init__(self, desc, device):
        super(GetRenderResolution, self).__init__(desc)
        self.device = device

    def execute(self):
        req = perfdog_pb2.GetRenderResolutionReq(device=self.device)
        print(get_stub().GetRenderResolutionOfWindowUnderTest(req))
        return Quit()


def get_top_menus():
    return [
        MonitorDevice('Monitor device disconnections'),
        PrintDevices('Print all currently connected devices'),
        GetDeviceStatus('Get device status'),
        InitDevice('Initialize device'),
        SetGlobalDataUploadServer('Configure third-party data storage services'),
        ClearGlobalDataUploadServer('Clear third-party data storage service configuration'),
        SetScreenShotInterval('Configure device screenshot interval'),
        EnableInstallApk('Installing the APK when setting up a test Android device'),
        DisableInstallApk('Setting up a test Android device without installing the APK'),
        SaveTestData('Save data'),
        GetDeviceCacheData('Single pull device cache data (press any key to end)'),
        GetDeviceCacheDataPacked('Pull device cache data in batches (press any key to end)'),
        CreateTask('Create tasks'),
        ArchiveCaseToTask('Archive Case to task'),
        ShareCase('Share Case'),
        KillServer('Kill Server'),
    ]
