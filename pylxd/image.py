# Copyright (c) 2015 Canonical Ltd
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
from __future__ import print_function
import datetime
import json
from six.moves import urllib

from pylxd import base
from pylxd import connection
from pylxd import exceptions

image_architecture = {
    0: 'Unknown',
    1: 'i686',
    2: 'x86_64',
    3: 'armv7l',
    4: 'aarch64',
    5: 'ppc',
    6: 'ppc64',
    7: 'ppc64le'
}


class LXDImage(base.LXDBase):

    def __init__(self, conn=None):
        self.connection = conn or connection.LXDConnection()

    # list images
    def image_list(self):
        try:
            (state, data) = self.connection.get_object('GET', '/1.0/images')
            return [image.split('/1.0/images/')[-1]
                    for image in data['metadata']]
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    def image_defined(self, image):
        try:
            (state, data) = self.connection.get_object('GET', '/1.0/images/%s'
                                                       % image)
        except exceptions.APIError as ex:
            if ex.status_code == 404:
                return False
            else:
                raise
        else:
            return True

    def image_list_by_key(self, params):
        try:
            (state, data) = self.connection.get_object(
                'GET', '/1.0/images', urllib.parse.urlencode(params))
            return [image.split('/1.0/images/')[-1]
                    for image in data['metadata']]
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    # image info
    def image_info(self, image):
        try:
            (state, data) = self.connection.get_object('GET', '/1.0/images/%s'
                                                       % image)
            image = {
                'image_upload_date': self.get_image_date(image,
                                                         data.get('metadata'),
                                                         'uploaded_at'),
                'image_created_date': self.get_image_date(image,
                                                          data.get('metadata'),
                                                          'created_at'),
                'image_expires_date': self.get_image_date(image,
                                                          data.get('metadata'),
                                                          'expires_at'),
                'image_public': self.get_image_permission(
                    image,
                    data.get('metadata')),
                'image_size': '%sMB' % self.get_image_size(
                    image,
                    data.get('metadata')),
                'image_fingerprint': self.get_image_fingerprint(
                    image,
                    data.get('metadata')),
                'image_architecture': self.get_image_architecture(
                    image,
                    data.get('metadata')),
            }

            return image
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    def get_image_date(self, image, data, key):
        try:
            if data is None:
                (state, data) = self.connection.get_object(
                    'GET', '/1.0/images/%s' % image)
                data = data.get('metadata')
            if data[key] != 0:
                return datetime.datetime.fromtimestamp(
                    data[key]).strftime('%Y-%m-%d %H:%M:%S')
            else:
                return 'Unknown'
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    def get_image_permission(self, image, data):
        try:
            if data is None:
                (state, data) = self.connection.get_object(
                    'GET', '/1.0/images/%s' % image)
                data = data.get('metadata')
            return True if data['public'] == 1 else False
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    def get_image_size(self, image, data):
        try:
            if data is None:
                (state, data) = self.connection.get_object(
                    'GET', '/1.0/images/%s' % image)
                data = data.get('metadata')
            image_size = data['size']
            if image_size <= 0:
                raise exceptions.ImageInvalidSize()
            return image_size // 1024 ** 2
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    def get_image_fingerprint(self, image, data):
        try:
            if data is None:
                (state, data) = self.connection.get_object(
                    'GET', '/1.0/images/%s' % image)
                data = data.get('metadata')
            return data['fingerprint']
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    def get_image_architecture(self, image, data):
        try:
            if data is None:
                (state, data) = self.connection.get_object(
                    'GET', '/1.0/images/%s' % image)
                data = data.get('metadata')
            return image_architecture[data['architecture']]
        except Exception as e:
            print("Unable to fetch image info - {}".format(e))
            raise

    # image operations
    def image_upload(self, path=None, data=None, headers={}):
        data = data or open(path, 'rb').read()
        try:
            return self.connection.get_object('POST', '/1.0/images',
                                              data, headers)
        except Exception as e:
            print("Unable to upload image - {}".format(e))
            raise

    def image_delete(self, image):
        try:
            return self.connection.get_status('DELETE', '/1.0/images/%s'
                                              % image)
        except Exception as e:
            print("Unable to delete image - {}".format(e))
            raise

    def image_export(self, image):
        try:
            return self.connection.get_raw('GET', '/1.0/images/%s/export'
                                           % image)
        except Exception as e:
            print("Unable to export image - {}".format(e))
            raise

    def image_update(self, image, data):
        try:
            return self.connection.get_status('PUT', '/1.0/images/%s' % image,
                                              json.dumps(data))
        except Exception as e:
            print("Unable to update image - {}".format(e))
            raise

    def image_rename(self, image, data):
        try:
            return self.connection.get_status('POST', '/1.0/images/%s' % image,
                                              json.dumps(data))
        except Exception as e:
            print("Unable to rename image - {}".format(e))
            raise


class LXDAlias(base.LXDBase):

    def alias_list(self):
        (state, data) = self.connection.get_object(
            'GET', '/1.0/images/aliases')
        return [alias.split('/1.0/images/aliases/')[-1]
                for alias in data['metadata']]

    def alias_defined(self, alias):
        return self.connection.get_status('GET', '/1.0/images/aliases/%s'
                                          % alias)

    def alias_show(self, alias):
        return self.connection.get_object('GET', '/1.0/images/aliases/%s'
                                          % alias)

    def alias_update(self, alias, data):
        return self.connection.get_status('PUT',
                                          '/1.0/images/aliases/%s' % alias,
                                          json.dumps(data))

    def alias_rename(self, alias, data):
        return self.connection.get_status('POST',
                                          '/1.0/images/aliases/%s' % alias,
                                          json.dumps(data))

    def alias_create(self, data):
        return self.connection.get_status('POST', '/1.0/images/aliases',
                                          json.dumps(data))

    def alias_delete(self, alias):
        return self.connection.get_status('DELETE', '/1.0/images/aliases/%s'
                                          % alias)

_lxd = connection.LXD()


class Image(object):
    """A LXD Image object."""

    __slots__ = [
        'aliases', 'architecture', 'created_at', 'expires_at', 'filename',
        'fingerprint', 'public', 'properties', 'size', 'uploaded_at']

    @classmethod
    def get(cls, fingerprint):
        """Get an image by fingerprint."""
        response = _lxd.images[fingerprint].get()

        image = cls()
        for key, value in response.json()['metadata'].iteritems():
            setattr(image, key, value)
        return image

    @classmethod
    def get_by_alias(cls, alias):
        """Get an image by its alias."""
        response = _lxd.images.aliases[alias].get()

        fingerprint = response.json()['metadata']['target']
        return cls.get(fingerprint)

    @classmethod
    def get_all(cls):
        """Get all images on an LXD host as Image objects."""
        response = _lxd.images.get()

        images = []
        for name in response.json()['metadata']:
            image = cls()
            image.fingerprint = name.split('/')[-1]
            images.append(image)
        return images

    @classmethod
    def create(cls, name):
        """Create a new Image."""

    def update(self):
        """Update an Image."""

    def rename(self):
        """Rename an Image."""

    def delete(self):
        """Delete an Image."""
        _lxd.images[self.fingerprint].delete()
