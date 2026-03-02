# SPDX-License-Identifier: BSD-2-Clause
""" Tests for the sourcetospec module. """

# Copyright (C) 2024, 2025 embedded brains GmbH & Co. KG
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
# POSSIBILITY OF SUCH DAMAGE.

from pathlib import Path

import pytest

from specmake import doxygen_xml_to_spec

_GF_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  gf_0().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes":
            None,
            "body":
            None,
            "params": [
                "const int *${.:/params[0]/name}", "int *${.:/params[1]/name}",
                "int *${.:/params[2]/name}", "int ${.:/params[3]/name}"
            ],
            "return":
            "int"
        },
        "variants": []
    },
    "description":
    "Description  gf_0().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gf_0",
    "notes":
    None,
    "params": [{
        "description": "gf_0() in description.",
        "dir": "in",
        "name": "in"
    }, {
        "description": "gf_0() out description.",
        "dir": "out",
        "name": "out"
    }, {
        "description": "gf_0() inout description.",
        "dir": "inout",
        "name": "inout"
    }, {
        "description": "gf_0() none description.",
        "dir": None,
        "name": "none"
    }],
    "return": {
        "return":
        "gf_0() return description.",
        "return-values": [{
            "description": "gf_0() retval description.",
            "value": "retval"
        }]
    },
    "type":
    "interface"
}

_F_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  f_0().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes":
            None,
            "body":
            None,
            "params": [
                "const int *${.:/params[0]/name}", "int *${.:/params[1]/name}",
                "int *${.:/params[2]/name}", "int ${.:/params[3]/name}",
                "int *(*${.:/params[4]/name})(int i, int *, int *(*f2)(void))"
            ],
            "return":
            "int"
        },
        "variants": []
    },
    "description":
    "Description  f_0().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "f_0",
    "notes":
    None,
    "params": [{
        "description": "f_0() in description.",
        "dir": "in",
        "name": "in"
    }, {
        "description": "f_0() out description.",
        "dir": "out",
        "name": "out"
    }, {
        "description": "f_0() inout description.",
        "dir": "inout",
        "name": "inout"
    }, {
        "description": "f_0() none description.",
        "dir": None,
        "name": "none"
    }, {
        "description": "f_0() function pointer description.",
        "dir": None,
        "name": "f"
    }],
    "return": {
        "return":
        "* f_0() return description list item 0\n\n"
        "* f_0() return description list item 1",
        "return-values": [{
            "description": "f_0() retval description.",
            "value": "retval"
        }]
    },
    "type":
    "interface"
}

_GF_1_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  gf_1().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes": None,
            "body": None,
            "params": [],
            "return": None
        },
        "variants": []
    },
    "description":
    "Description  gf_1().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gf_1",
    "notes":
    None,
    "params": [],
    "return":
    None,
    "type":
    "interface"
}

_F_1_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  f_1().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes": None,
            "body": None,
            "params": [],
            "return": None
        },
        "variants": []
    },
    "description":
    "Description  f_1().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "f_1",
    "notes":
    None,
    "params": [],
    "return":
    None,
    "type":
    "interface"
}

_GF_2_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief gf_2().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes": None,
            "body": None,
            "params": ["int ${.:/params[0]/name}", "int ${.:/params[1]/name}"],
            "return": "int"
        },
        "variants": []
    },
    "description":
    "Description gf_2().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gf_2",
    "notes":
    None,
    "params": [{
        "description": "gf_2() x description.",
        "dir": "in",
        "name": "x"
    }, {
        "description": "gf_2() y description.",
        "dir": "in",
        "name": "y"
    }],
    "return": {
        "return":
        "gf_2() return description.",
        "return-values": [{
            "description": "gf_2() retval description.",
            "value": "retval"
        }]
    },
    "type":
    "interface"
}

_F_2_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief f_2().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes": None,
            "body": None,
            "params": ["int ${.:/params[0]/name}", "int ${.:/params[1]/name}"],
            "return": "int"
        },
        "variants": []
    },
    "description":
    "Description f_2().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "f_2",
    "notes":
    None,
    "params": [{
        "description": "f_2() x description.",
        "dir": "in",
        "name": "x"
    }, {
        "description": "f_2() y description.",
        "dir": "in",
        "name": "y"
    }],
    "return": {
        "return":
        "f_2() return description.",
        "return-values": [{
            "description": "f_2() retval description.",
            "value": "retval"
        }]
    },
    "type":
    "interface"
}

_GF_3_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    None,
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes": None,
            "body": None,
            "params": ["int ${.:/params[0]/name}", "int ${.:/params[1]/name}"],
            "return": None
        },
        "variants": []
    },
    "description":
    None,
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gf_3",
    "notes":
    None,
    "params": [{
        "description": None,
        "dir": None,
        "name": "x",
    }, {
        "description": None,
        "dir": None,
        "name": "y",
    }],
    "return":
    None,
    "type":
    "interface"
}

_GF_4_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  gf_4().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes":
            None,
            "body":
            None,
            "params":
            ["const int *${.:/params[0]/name}", "int *${.:/params[1]/name}"],
            "return":
            "int"
        },
        "variants": []
    },
    "description":
    "Description  gf_4().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "function",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gf_4",
    "notes":
    None,
    "params": [{
        "description": "gf_4() in description.",
        "dir": "in",
        "name": "in"
    }, {
        "description": "gf_4() out description.",
        "dir": "out",
        "name": "out"
    }],
    "return": {
        "return": "gf_4() return description.",
        "return-values": []
    },
    "type":
    "interface"
}

_GM_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  GM_0().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes": None,
            "body": "((a) > (b) ? (a) : (b))",
            "params": ["${.:/params[0]/name}", "${.:/params[1]/name}"],
            "return": None
        },
        "variants": []
    },
    "description":
    "Description  GM_0().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "macro",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "GM_0",
    "notes":
    None,
    "params": [{
        "description": "GM_0() a description.",
        "dir": "in",
        "name": "a"
    }, {
        "description": "GM_0() b description.",
        "dir": "in",
        "name": "b"
    }],
    "return": {
        "return": "GM_0() return description.",
        "return-values": []
    },
    "type":
    "interface"
}

_M_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  M_0().",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": {
            "attributes": None,
            "body": "((a) < (b) ? (a) : (b))",
            "params": ["${.:/params[0]/name}", "${.:/params[1]/name}"],
            "return": None
        },
        "variants": []
    },
    "description":
    "Description  M_0().",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "macro",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "M_0",
    "notes":
    None,
    "params": [{
        "description": "M_0() a description.",
        "dir": "in",
        "name": "a"
    }, {
        "description": "M_0() b description.",
        "dir": "in",
        "name": "b"
    }],
    "return": {
        "return": "M_0() return description.",
        "return-values": []
    },
    "type":
    "interface"
}

_GD_1_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief GD_1.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": "4096",
        "variants": []
    },
    "description":
    None,
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "define",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "GD_1",
    "notes":
    None,
    "type":
    "interface"
}

_D_1_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief D_1.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": {
        "default": "1024",
        "variants": []
    },
    "description":
    None,
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "define",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "D_1",
    "notes":
    None,
    "type":
    "interface"
}

_GT_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  gt_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "x"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "y"
        },
        "variants": []
    }],
    "definition-kind":
    "typedef-only",
    "description":
    "Description  gt_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "struct",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gt_0",
    "notes":
    None,
    "type":
    "interface"
}

_T_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  t_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "x"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "y"
        },
        "variants": []
    }],
    "definition-kind":
    "typedef-only",
    "description":
    "Description  t_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "struct",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "t_0",
    "notes":
    None,
    "type":
    "interface"
}

_GS_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  gs_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "a"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "b"
        },
        "variants": []
    }],
    "definition-kind":
    "struct-only",
    "description":
    "Description  gs_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "struct",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gs_0",
    "notes":
    None,
    "type":
    "interface"
}

_S_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  s_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "a"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "b"
        },
        "variants": []
    }],
    "definition-kind":
    "struct-only",
    "description":
    "Description  s_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "struct",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "s_0",
    "notes":
    None,
    "type":
    "interface"
}

_GU_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  gu_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "i"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "float ${.:name}",
            "description": None,
            "kind": "member",
            "name": "f"
        },
        "variants": []
    }],
    "definition-kind":
    "typedef-only",
    "description":
    "Description  gu_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "union",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gu_0",
    "notes":
    None,
    "type":
    "interface"
}

_U_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  u_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "char ${.:name}",
            "description": None,
            "kind": "member",
            "name": "c"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "i"
        },
        "variants": []
    }],
    "definition-kind":
    "typedef-only",
    "description":
    "Description  u_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "union",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "u_0",
    "notes":
    None,
    "type":
    "interface"
}

_GU_1_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  gu_1.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "i"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "float ${.:name}",
            "description": None,
            "kind": "member",
            "name": "f"
        },
        "variants": []
    }],
    "definition-kind":
    "union-only",
    "description":
    "Description  gu_1.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "union",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "gu_1",
    "notes":
    None,
    "type":
    "interface"
}

_U_1_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief  u_1.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition": [{
        "default": {
            "brief": None,
            "definition": "char ${.:name}",
            "description": None,
            "kind": "member",
            "name": "c"
        },
        "variants": []
    }, {
        "default": {
            "brief": None,
            "definition": "int ${.:name}",
            "description": None,
            "kind": "member",
            "name": "i"
        },
        "variants": []
    }],
    "definition-kind":
    "union-only",
    "description":
    "Description  u_1.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "union",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }],
    "name":
    "u_1",
    "notes":
    None,
    "type":
    "interface"
}

_GE_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief ge_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition-kind":
    "typedef-only",
    "description":
    "Description ge_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "enum",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }, {
        "role": "interface-enumerator",
        "uid": "ge-0-a"
    }, {
        "role": "interface-enumerator",
        "uid": "ge-0-b"
    }, {
        "role": "interface-enumerator",
        "uid": "ge-0-c"
    }],
    "name":
    "ge_0",
    "notes":
    None,
    "type":
    "interface"
}

_E_0_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief e_0.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition-kind":
    "typedef-and-enum",
    "description":
    "Description e_0.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "enum",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }, {
        "role": "interface-enumerator",
        "uid": "e-0-a"
    }],
    "name":
    "e_0",
    "notes":
    None,
    "type":
    "interface"
}

_E_1_EXPECTED_RESULT = {
    "SPDX-License-Identifier":
    "CC-BY-SA-4.0 OR BSD-2-Clause",
    "brief":
    "Brief e_1.",
    "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"],
    "definition-kind":
    "enum-only",
    "description":
    "Description e_1.",
    "enabled-by":
    True,
    "index-entries": [],
    "interface-type":
    "enum",
    "links": [{
        "role": "interface-placement",
        "uid": "header-header"
    }, {
        "role": "interface-ingroup",
        "uid": "group"
    }, {
        "role": "interface-enumerator",
        "uid": "e-1-a"
    }],
    "name":
    "e_1",
    "notes":
    None,
    "type":
    "interface"
}


def _enumvalue(name: str) -> dict:
    return {
        "SPDX-License-Identifier": "CC-BY-SA-4.0 OR BSD-2-Clause",
        "brief": f"Brief {name}.",
        "copyrights": [
            "Copyright (C) 2024 embedded brains GmbH & Co. KG",
        ],
        "description": f"Description {name}.",
        "enabled-by": True,
        "index-entries": [],
        "interface-type": "enumerator",
        "links": [],
        "name": name,
        "notes": None,
        "type": "interface"
    }


_RESULTS = {
    "function": {
        "f_0": _F_0_EXPECTED_RESULT,
        "f_1": _F_1_EXPECTED_RESULT,
        "f_2": _F_2_EXPECTED_RESULT,
        "gf_0": _GF_0_EXPECTED_RESULT,
        "gf_1": _GF_1_EXPECTED_RESULT,
        "gf_2": _GF_2_EXPECTED_RESULT,
        "gf_3": _GF_3_EXPECTED_RESULT,
        "gf_4": _GF_4_EXPECTED_RESULT,
    },
    "define": {
        "M_0": _M_0_EXPECTED_RESULT,
        "GM_0": _GM_0_EXPECTED_RESULT,
        "D_1": _D_1_EXPECTED_RESULT,
        "GD_1": _GD_1_EXPECTED_RESULT,
    },
    "struct": {
        "s_0": _S_0_EXPECTED_RESULT,
        "gs_0": _GS_0_EXPECTED_RESULT,
        "t_0": _T_0_EXPECTED_RESULT,
        "gt_0": _GT_0_EXPECTED_RESULT,
    },
    "union": {
        "u_0": _U_0_EXPECTED_RESULT,
        "gu_0": _GU_0_EXPECTED_RESULT,
        "u_1": _U_1_EXPECTED_RESULT,
        "gu_1": _GU_1_EXPECTED_RESULT,
    },
    "enum": {
        "e_0": _E_0_EXPECTED_RESULT,
        "ge_0": _GE_0_EXPECTED_RESULT,
        "e_1": _E_1_EXPECTED_RESULT,
    },
    "enumvalue": {
        "GE_0_A": _enumvalue("GE_0_A"),
        "GE_0_B": _enumvalue("GE_0_B"),
        "GE_0_C": _enumvalue("GE_0_C"),
        "E_0_A": _enumvalue("E_0_A"),
        "E_1_A": _enumvalue("E_1_A")
    }
}


def _get_path(path: str) -> str:
    test_dir = Path(__file__).parent
    return str(test_dir / f"{path}")


def test_doxygen_xml_to_spec():
    xml_files = [
        _get_path("source-to-spec/xml/bad_8c.xml"),
        _get_path("source-to-spec/xml/header_8h.xml"),
        _get_path("source-to-spec/xml/foobar_8h.xml"),
        _get_path("source-to-spec/xml/group__FooGroup.xml"),
        _get_path("source-to-spec/xml/source_8c.xml"),
        _get_path("source-to-spec/xml/structs__0.xml"),
        _get_path("source-to-spec/xml/structgs__0.xml"),
        _get_path("source-to-spec/xml/structt__0.xml"),
        _get_path("source-to-spec/xml/structgt__0.xml"),
        _get_path("source-to-spec/xml/unionu__0.xml"),
        _get_path("source-to-spec/xml/uniongu__0.xml"),
        _get_path("source-to-spec/xml/unionu__1.xml"),
        _get_path("source-to-spec/xml/uniongu__1.xml")
    ]
    config = {
        "data": {
            "copyrights": ["Copyright (C) 2024 embedded brains GmbH & Co. KG"]
        },
        "groups": {
            "group__FooGroup": {
                "uid": "/if/group",
                "remove-prefix": "foobar-"
            }
        }
    }
    ctx = doxygen_xml_to_spec(config, xml_files)
    for kind, name_result in _RESULTS.items():
        for name, result in name_result.items():
            assert result == ctx.items_by_name[kind][name][0].export()
    u_0 = ctx.items["unionu__0"]
    assert u_0 < ctx.items["unionu__1"]
    assert not u_0.is_header
    assert u_0.uid == "/if/u-0"
    header = ctx.items["header_8h"]
    assert header.is_header
    assert header.uid == "/if/header-header"
    foobar = ctx.items["foobar_8h"]
    assert foobar.is_header
    assert foobar.uid == "/if/header"
    source = ctx.items["source_8c"]
    assert not source.is_header
    assert source.uid == "/if/source-c"
    bad_f = ctx.items["bad_8c_1a8cc687906d3e4964fc993ca1bf18472e"]
    with pytest.raises(ValueError):
        bad_f.group
    assert not bad_f.is_header
