# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Compatibility patch for Flask-AppBuilder with marshmallow 4.x.

Flask-AppBuilder auto-generates marshmallow-sqlalchemy schemas for its
security models.  In marshmallow 4.x, foreign-key columns are no longer
included by default, which causes ``KeyError`` during schema
initialisation (e.g. ``KeyError: 'permission_id'``).

This module monkey-patches ``marshmallow.Schema._init_fields`` so that
any ``KeyError`` raised during field resolution is handled by
dynamically injecting the missing field as a ``fields.Raw`` stub and
retrying.  The patch is safe to apply on marshmallow 3.x (it simply
never triggers) and will be unnecessary once Flask-AppBuilder ships a
native fix.
"""

from __future__ import annotations

import logging
from importlib.metadata import version as pkg_version
from typing import Any

from marshmallow import fields, Schema

logger = logging.getLogger(__name__)

_ORIGINAL_INIT_FIELDS: Any = None
_MAX_RETRIES = 20


def _patched_init_fields(self: Schema) -> None:
    """Wrapper around ``Schema._init_fields`` that catches ``KeyError``
    from missing FK columns and injects stub ``fields.Raw`` instances."""
    retries = 0
    while retries < _MAX_RETRIES:
        try:
            _ORIGINAL_INIT_FIELDS(self)
            return
        except KeyError as exc:
            missing_key = str(exc).strip("'\"")
            if not missing_key:
                raise
            logger.debug(
                "Injecting missing field %r into %s for FAB compatibility",
                missing_key,
                type(self).__name__,
            )
            stub = fields.Raw(dump_default=None, load_default=None)
            type(self)._declared_fields[missing_key] = stub
            self.declared_fields[missing_key] = stub
            retries += 1
    raise RuntimeError(
        f"Failed to initialise schema {type(self).__name__} after "
        f"{_MAX_RETRIES} retries — too many missing fields."
    )


def patch_marshmallow_for_flask_appbuilder() -> None:
    """Apply the compatibility patch (idempotent)."""
    global _ORIGINAL_INIT_FIELDS  # noqa: PLW0603

    if _ORIGINAL_INIT_FIELDS is not None:
        return

    major = int(pkg_version("marshmallow").split(".")[0])
    if major < 4:
        return

    _ORIGINAL_INIT_FIELDS = Schema._init_fields
    Schema._init_fields = _patched_init_fields
    logger.info("Applied marshmallow 4.x compatibility patch for Flask-AppBuilder")
