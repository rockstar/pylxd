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

from pylxd.image import Image

from integration.testing import IntegrationTestCase


class Test10Images(IntegrationTestCase):
    """Tests for /1.0/images"""

    def test_1_0_images_POST(self):
        """Return: list of URLs for images this server publishes."""
        response = self.lxd.images.post(json={
            'public': True,
            'source': {
                'type': 'url',
                'server': 'http://example.com',
                'alias': 'test-image'
                }})

        self.assertEqual(202, response.status_code)


class ImageTestCase(IntegrationTestCase):
    """An Image test case."""

    def setUp(self):
        super(ImageTestCase, self).setUp()
        self.fingerprint = self.create_image()

    def tearDown(self):
        super(ImageTestCase, self).tearDown()
        self.delete_image(self.fingerprint)


class Test10Image(ImageTestCase):
    """Tests for /1.0/images/<fingerprint>."""

    @unittest.skip("Not yet implemented in LXD")
    def test_1_0_images_name_POST(self):
        """Return: dict representing an image properties."""
        response = self.lxd.images[self.fingerprint].post(json={
            'name': 'test-image'
            })

        self.assertEqual(200, response.status_code)

    def test_1_0_images_name_PUT(self):
        """Return: dict representing an image properties."""
        response = self.lxd.images[self.fingerprint].put(json={
            'public': False
            })

        self.assertEqual(200, response.status_code)


class Test10ImageExport(ImageTestCase):
    """Tests for /1.0/images/<fingerprint>/export."""

    def test_1_0_images_export(self):
        """Return: dict representing an image properties."""
        response = self.lxd.images[self.fingerprint].export.get()

        self.assertEqual(200, response.status_code)


class Test10ImageSecret(ImageTestCase):
    """Tests for /1.0/images/<fingerprint>/secret."""

    def test_1_0_images_secret(self):
        """Return: dict representing an image properties."""
        response = self.lxd.images[self.fingerprint].secret.post({
            'name': 'abcdef'
            })

        self.assertEqual(202, response.status_code)


class Test10ImageAliases(IntegrationTestCase):
    """Tests for /1.0/images/aliases."""

    def test_1_0_images_aliases(self):
        """Return: list of URLs for images this server publishes."""
        response = self.lxd.images.aliases.get()

        self.assertEqual(200, response.status_code)

    def test_1_0_images_aliases_POST(self):
        """Return: list of URLs for images this server publishes."""
        fingerprint = self.create_image()
        alias = 'test-alias'
        self.addCleanup(self.delete_image, alias)
        response = self.lxd.images.aliases.post(json={
            'target': fingerprint,
            'name': alias
            })

        self.assertEqual(200, response.status_code)


class Test10ImageAlias(ImageTestCase):
    """Tests for /1.0/images/aliases/<alias>."""

    def setUp(self):
        super(Test10ImageAlias, self).setUp()
        self.alias = self.create_alias(self.fingerprint)

    def test_GET(self):
        """Return: dict representing an alias description or target."""
        response = self.lxd.images.aliases[self.alias].get()

        self.assertEqual(200, response.status_code)

    @unittest.skip("Not yet implemented in LXD")
    def test_PUT(self):
        """Return: dict representing an alias description or target."""
        self.create_alias(self.fingerprint)

        response = self.lxd.images.aliases[self.alias].put(json={
            'description': 'An container alias',
            'target': self.fingerprint
            })

        self.assertEqual(200, response.status_code)

    @unittest.skip("Not yet implemented in LXD")
    def test_POST(self):
        """Return: dict representing an alias description or target."""
        self.create_alias(self.fingerprint)

        response = self.lxd.images.aliases[self.alias].post(json={
            'name': self.alias[:-1]
            })

        self.assertEqual(200, response.status_code)

    def test_DELETE(self):
        """Return: dict representing an alias description or target."""
        self.create_alias(self.fingerprint)

        response = self.lxd.images.aliases[self.alias].delete()

        self.assertEqual(200, response.status_code)


class TestImage(IntegrationTestCase):
    """Tests for pylxd.image.Image."""

    def test_get_all(self):
        """Returns a list of all images."""
        fingerprint = self.create_image()
        self.addCleanup(self.delete_image, fingerprint)

        images = Image.get_all()

        self.assertIn(fingerprint, [i.fingerprint for i in images])

    def test_get(self):
        """Returns an Image by its fingerprint."""
        fingerprint = self.create_image()
        self.addCleanup(self.delete_image, fingerprint)

        image = Image.get(fingerprint)

        self.assertEqual(fingerprint, image.fingerprint)
        self.assertEqual(
            [{'description': 'testget',
              'target': 'testget'}],
            image.aliases)
        self.assertEqual(2, image.architecture)
        self.assertIsNotNone(image.created_at)
        self.assertEqual(0, image.expires_at)
        self.assertEqual('', image.filename)
        self.assertEqual(1, image.public)
        self.assertEqual(
            ['architecture', 'description', 'name', 'obfuscate', 'os'],
            sorted(image.properties.keys()))
        self.assertIsNotNone(image.size)
        self.assertIsNotNone(image.uploaded_at)

    def test_get_by_alias(self):
        """Returns an Image by its alias."""
        fingerprint, alias = self.create_image(return_alias=True)
        self.addCleanup(self.delete_image, fingerprint)

        image = Image.get_by_alias(alias)

        self.assertEqual(fingerprint, image.fingerprint)

    def test_create(self):
        """Creates an Image."""

    def test_update(self):
        """Updates an Image."""
        fingerprint = self.create_image()
        self.addCleanup(self.delete_container, fingerprint)
        image = Image.get(fingerprint)

        image.update({})

    def test_rename(self):
        """Renames an existing Image."""
        fingerprint = self.create_image()
        self.addCleanup(self.delete_container, fingerprint)
        image = Image.get(fingerprint)

        image.rename()

    def test_delete(self):
        """Deletes an Image."""
        fingerprint = self.create_image()
        self.addCleanup(self.delete_container, fingerprint)
        image = Image.get(fingerprint)

        image.delete()
        response = self.lxd.images[fingerprint].get()

        self.assertEqual(404, response.status_code)
