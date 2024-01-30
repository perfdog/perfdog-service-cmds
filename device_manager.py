# coding: utf-8
import threading

import perfdog_pb2


class DeviceManager(object):
    def __init__(self, stub):
        self.stub = stub

    def start_monitor(self, listener):
        event_stream = self.stub.startDeviceMonitor(perfdog_pb2.Empty())

        def run():
            try:
                for device_event in event_stream:
                    event_type = device_event.eventType
                    device = device_event.device
                    if event_type == perfdog_pb2.ADD:
                        listener.on_add_device(device)
                    elif event_type == perfdog_pb2.REMOVE:
                        listener.on_remove_device(device)
            except Exception as e:
                print(e)

        t = threading.Thread(target=run)
        t.setDaemon(True)
        t.start()

        return event_stream

    @staticmethod
    def stop_monitor(event_stream):
        event_stream.cancel()

    def on_add_device(self, device):
        self.devices.append(device)

        if self.listener is not None:
            self.listener.on_add_device(device)

    def on_remove_device(self, device):
        for d in self.devices:
            if d.conType == device.conType and d.uid == device.uid:
                self.devices.remove(d)
                break

        if self.listener is not None:
            self.listener.on_remove_device(device)

    def print_devices(self):
        res = self.stub.getDeviceList(perfdog_pb2.Empty())
        index = 0
        for device in res.devices:
            print('Devices[%s]:' % index)
            print(device)
            index += 1

    def select_device(self):
        res = self.stub.getDeviceList(perfdog_pb2.Empty())
        index = 0
        for device in res.devices:
            print('Devices[%s]:' % index)
            print(device)
            index += 1
        idx = int(input('Please select the corresponding device:'))
        return res.devices[idx]
