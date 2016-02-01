# Copyright (c) 2016 Canonical Ltd
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
from pylxd import container

from integration.testing import IntegrationTestCase


class ContainerTestCase(IntegrationTestCase):
    """A Container-specific test case."""

    def setUp(self):
        super(ContainerTestCase, self).setUp()
        self.name = self.create_container()

    def tearDown(self):
        super(ContainerTestCase, self).tearDown()
        self.delete_container(self.name)


class Test10ContainerState(ContainerTestCase):
    """Tests for /1.0/containers/<name>/state."""

    def test_GET(self):
        """Return: dict representing current state."""
        result = self.lxd.containers[self.name].state.get()

        self.assertEqual(200, result.status_code)

    def test_PUT(self):
        """Return: background operation or standard error."""
        result = self.lxd.containers[self.name].state.put(json={
            'action': 'freeze',
            'timeout': 30,
            })

        self.assertEqual(202, result.status_code)


class Test10ContainerFiles(ContainerTestCase):
    """Tests for /1.0/containers/<name>/files."""

    def test10containerfiles(self):
        """Return: dict representing current files."""
        result = self.lxd.containers[self.name].files.get(params={
            'path': '/bin/sh'
            })

        self.assertEqual(200, result.status_code)

    def test10containerfiles_POST(self):
        """Return: standard return value or standard error."""
        result = self.lxd.containers[self.name].files.get(params={
            'path': '/bin/sh'
            }, data='abcdef')

        self.assertEqual(200, result.status_code)


class Test10ContainerSnapshots(ContainerTestCase):
    """Tests for /1.0/containers/<name>/snapshots."""

    def test10containersnapshots(self):
        """Return: list of URLs for snapshots for this container."""
        result = self.lxd.containers[self.name].snapshots.get()

        self.assertEqual(200, result.status_code)

    def test10containersnapshots_POST(self):
        """Return: background operation or standard error."""
        result = self.lxd.containers[self.name].snapshots.post(json={
            'name': 'test-snapshot',
            'stateful': False
            })

        self.assertEqual(202, result.status_code)


class Test10ContainerSnapshot(ContainerTestCase):
    """Tests for /1.0/containers/<name>/snapshot/<name>."""

    def setUp(self):
        super(Test10ContainerSnapshot, self).setUp()
        result = self.lxd.containers[self.name].snapshots.post(json={
            'name': 'test-snapshot', 'stateful': False})
        operation_uuid = result.json()['operation'].split('/')[-1]
        result = self.lxd.operations[operation_uuid].wait.get()

    def test10containersnapshot(self):
        """Return: dict representing the snapshot."""
        result = self.lxd.containers[self.name].snapshots['test-snapshot'].get()

        self.assertEqual(200, result.status_code)

    def test10containersnapshot_POST(self):
        """Return: dict representing the snapshot."""
        result = self.lxd.containers[self.name].snapshots['test-snapshot'].post(json={
            'name': 'test-snapshot.bak-lol'
            })

        self.assertEqual(202, result.status_code)

    def test10containersnapshot_DELETE(self):
        """Return: dict representing the snapshot."""
        result = self.lxd.containers[self.name].snapshots['test-snapshot'].delete()

        self.assertEqual(202, result.status_code)


class Test10ContainerExec(ContainerTestCase):
    """Tests for /1.0/containers/<name>/exec."""

    def setUp(self):
        super(Test10ContainerExec, self).setUp()

        result = self.lxd.containers[self.name].state.put(json={
            'action': 'start', 'timeout': 30, 'force': True})
        operation_uuid = result.json()['operation'].split('/')[-1]
        self.lxd.operations[operation_uuid].wait.get()
        self.addCleanup(self.stop_container)

    def stop_container(self):
        """Stop the container (before deleting it)."""
        result = self.lxd.containers[self.name].state.put(json={
            'action': 'stop', 'timeout': 30, 'force': True})
        operation_uuid = result.json()['operation'].split('/')[-1]
        self.lxd.operations[operation_uuid].wait.get()

    def test10containerexec(self):
        """Return: background operation + optional websocket information.

        ...or standard error."""
        result = self.lxd.containers[self.name]['exec'].post(json={
            'command': ['/bin/bash'],
            'wait-for-websocket': False,
            'interactive': True,
            })

        self.assertEqual(202, result.status_code)


class Test10ContainerLogs(ContainerTestCase):
    """Tests for /1.0/containers/<name>/logs."""

    def test10containerlogs(self):
        """Return: a list of the available log files."""
        result = self.lxd.containers[self.name].logs.get()

        self.assertEqual(200, result.status_code)


class Test10ContainerLog(ContainerTestCase):
    """Tests for /1.0/containers/<name>/logs/<logfile>."""

    def setUp(self):
        super(Test10ContainerLog, self).setUp()
        result = self.lxd.containers[self.name].logs.get()
        self.log_name = result.json()['metadata'][0]['name']

    def test10containerlog(self):
        """Return: the contents of the log file."""
        result = self.lxd.containers[self.name].logs[self.log_name].get()

        self.assertEqual(200, result.status_code)

    def test10containerlog_DELETE(self):
        """Return: the contents of the log file."""
        result = self.lxd.containers[self.name].logs[self.log_name].delete()

        self.assertEqual(200, result.status_code)


class TestContainer(IntegrationTestCase):
    """Tests for pylxd.container.Container."""

    def test_get_all(self):
        """Container.get_all returns a list of Container objects."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        containers = container.Container.get_all()

        self.assertEqual(1, len(containers))
        self.assertEqual(name, containers[0].name)

    def test_get(self):
        """Container.get returns a Container populated with attributes."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)

        an_container = container.Container.get(name)

        self.assertEqual(2, an_container.architecture)
        self.assertEqual(
            ['limits.cpu', 'volatile.base_image', 'volatile.eth0.hwaddr',
             'volatile.eth0.name', 'volatile.last_state.idmap'],
            sorted(an_container.config.keys()))
        self.assertEqual({}, an_container.devices)
        self.assertEqual(True, an_container.ephemeral)
        self.assertEqual(
            ['limits.cpu', 'volatile.base_image', 'volatile.eth0.hwaddr',
             'volatile.eth0.name', 'volatile.last_state.idmap'],
            sorted(an_container.expanded_config.keys()))
        self.assertEqual(['eth0'], an_container.expanded_devices.keys())
        self.assertEqual(name, an_container.name)
        self.assertEqual(['default'], an_container.profiles)
        self.assertEqual(
            ['init', 'ips', 'processcount', 'status', 'status_code'],
            sorted(an_container.status.keys()))

    def test_create(self):
        """A Container is created on the machine."""
        name = 'an-container'
        self.addCleanup(self.delete_container, name)
        options = {
            'architecture': 2,
            'profiles': ['default'],
            'ephemeral': True,
            'config': {'limits.cpu': '2'},
            'source': {'type': 'image',
                       'alias': 'busybox'},
        }

        an_container = container.Container.create(name, options)

        self.assertEqual(name, an_container.name)

    def test_update(self):
        """An existing Container is updated."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)
        an_container = container.Container.get(name)

        an_container.update({'limits.cpu': '10'}, wait=True)
        response = self.lxd.containers[name].get()

        self.assertEqual('10', response.json()['metadata']['config']['limits.cpu'])

    def test_rename(self):
        """An existing Container is renamed."""
        new_name = 'an-container'
        name = self.create_container()
        self.addCleanup(self.delete_container, name)
        an_container = container.Container.get(name)

        an_container.rename(new_name)
        self.addCleanup(self.delete_container, new_name)
        response = self.lxd.containers[name].get()

        self.assertEqual(200, response.status_code)

    def test_delete(self):
        """An existing Container is deleted."""
        name = self.create_container()
        self.addCleanup(self.delete_container, name)
        an_container = container.Container.get(name)

        an_container.delete(wait=True)
        response = self.lxd.containers[name].get()

        self.assertEqual(404, response.status_code)
