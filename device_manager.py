# coding: utf-8
import threading

import perfdog_pb2


class DeviceManager(object):
    def __init__(self, stub):
        self.stub = stub
        self.devices = []
        self.device_event_stream = None
        self.listener = None

    def set_device_listener(self, listener):
        self.listener = listener

    def start(self):
        self.devices = []
        self.device_event_stream = self.stub.startDeviceMonitor(perfdog_pb2.Empty())
        t = threading.Thread(target=self.run)
        t.setDaemon(True)
        t.start()

    def stop(self):
        self.device_event_stream.cancel()
        self.device_event_stream = None
        self.devices = []

    def run(self):
        try:
            for device_event in self.device_event_stream:
                event_type = device_event.eventType
                device = device_event.device
                if event_type == perfdog_pb2.ADD:
                    self.on_add_device(device)
                elif event_type == perfdog_pb2.REMOVE:
                    self.on_remove_device(device)
        except Exception as e:
            print(e)

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
        index = 0
        for device in self.devices:
            print('Devices[%s]:' % index)
            print(device)
            index += 1

    def get_device(self, index):
        return self.devices[index]
