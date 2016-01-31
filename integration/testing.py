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
import unittest
import uuid

from pylxd.api import LXD
from integration.busybox import create_busybox_image


class IntegrationTestCase(unittest.TestCase):
    """A base test case for pylxd integration tests."""

    PARTS = []

    def setUp(self):
        super(IntegrationTestCase, self).setUp()
        self.lxd = self._lxd_root = LXD('http+unix://%2Fvar%2Flib%2Flxd%2Funix.socket')

        for part in self.PARTS:
            self.lxd = self.lxd[part]

    def create_container(self):
        """Create a container in lxd."""
        name = self.id().split('.')[-1].replace('_', '')
        machine = {
            'name': name,
            'architecture': 2,
            'profiles': ['default'],
            'ephemeral': True,
            'config': {'limits.cpu': '2'},
            'source': {'type': 'image',
                       'alias': 'busybox'},
        }
        result = self._lxd_root['1.0']['containers'].post(json=machine)
        operation_uuid = result.json()['operation'].split('/')[-1]
        result = self._lxd_root['1.0'].operations[operation_uuid].wait.get()

        self.addCleanup(self.delete_container, name)
        return name

    def delete_container(self, name, enforce=False):
        """Delete a container in lxd."""
        # enforce is a hack. There's a race somewhere in the delete.
        # To ensure we don't get an infinite loop, let's count.
        count = 0
        result = self._lxd_root['1.0']['containers'][name].delete()
        while enforce and result.status_code == 404 and count < 10:
            result = self._lxd_root['1.0']['containers'][name].delete()
            count += 1
        try:
            operation_uuid = result.json()['operation'].split('/')[-1]
            result = self._lxd_root['1.0'].operations[operation_uuid].wait.get()
        except KeyError:
            pass  # 404 cases are okay.

    def create_image(self):
        """Create an image in lxd."""
        path, fingerprint = create_busybox_image()
        with open(path, 'rb') as f:
            headers = {
                'X-LXD-Public': '1',
                }
            response = self._lxd_root['1.0'].images.post(data=f.read(), headers=headers)
        operation_uuid = response.json()['operation'].split('/')[-1]
        self._lxd_root['1.0'].operations[operation_uuid].wait.get()

        self.addCleanup(self.delete_image, fingerprint)
        return fingerprint

    def delete_image(self, fingerprint):
        """Delete an image in lxd."""
        self._lxd_root['1.0'].images[fingerprint].delete()

    def create_alias(self, fingerprint):
        # XXX: rockstar (31 Jan 2016) - it's possible we'll have to delete these,
        # thaugh if the image deletion doesn't also delete aliases, that would
        # be very odd indeed.
        alias = str(uuid.uuid4()).split('-')[0]
        self._lxd_root['1.0'].images.aliases.post(json={
            'target': fingerprint,
            'name': alias
            })
        return alias

    def assertCommon(self, response):
        """Assert common LXD responses.

        LXD responses are relatively standard. This function makes assertions
        to all those standards.
        """
        self.assertEqual(response.status_code, response.json()['status_code'])
        self.assertEqual(
            ['metadata', 'operation', 'status', 'status_code', 'type'],
            sorted(response.json().keys()))
