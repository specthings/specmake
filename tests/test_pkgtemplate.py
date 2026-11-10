# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the pkgtemplate module. """

# Copyright (C) 2026 embedded brains GmbH & Co. KG
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE

from specmake.pkgtemplate import _attribute_action


class _Item:
    uid = "/i"

    def substitute(self, value):
        return value


def test_attribute_action_selection_path():
    data = {
        "links": [{
            "uid": "a"
        }, {
            "uid": "b"
        }, {
            "uid": "a"
        }],
        "x": {
            "y": 1,
            "z": 2
        }
    }
    _attribute_action(_Item(), {
        "action": "remove",
        "path": "/links[attr(uid)='a']"
    }, data)
    assert data["links"] == [{"uid": "b"}]
    _attribute_action(_Item(), {
        "action": "set",
        "path": ["/x/*", "/w"],
        "value": 0
    }, data)
    assert data == {"links": [{"uid": "b"}], "w": 0, "x": {"y": 0, "z": 0}}
