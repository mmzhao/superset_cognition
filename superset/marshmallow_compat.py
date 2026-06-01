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
"""Compatibility layer for Flask-AppBuilder with marshmallow 4.x.

Flask-AppBuilder auto-generates marshmallow schema fields for SQLAlchemy
relationships (foreign-key columns like ``permission_id``, ``view_menu_id``,
etc.).  marshmallow 4 raises ``KeyError`` when these auto-generated fields
reference columns that are not declared on the schema.

This module monkey-patches ``marshmallow.Schema._init_fields`` so that any
missing foreign-key field is silently added as a ``Raw`` field with sensible
defaults, allowing Flask-AppBuilder's auto-generated schemas to initialize
without errors.

The patch is idempotent: calling ``patch_marshmallow_for_fab()`` more than
once is safe.
"""

from __future__ import annotations

import logging
from importlib.metadata import version as pkg_version

from marshmallow import fields, Schema

logger = logging.getLogger(__name__)

_PATCHED = False

# Foreign-key field names that Flask-AppBuilder auto-generates.
_FAB_FK_FIELD_NAMES: set[str] = {
    "chart_id",
    "dashboard_id",
    "database_id",
    "db_id",
    "permission_id",
    "user_id",
    "view_menu_id",
}


def _is_marshmallow_4() -> bool:
    """Return True when running on marshmallow 4+."""
    major, *_ = pkg_version("marshmallow").split(".")
    return int(major) >= 4


def patch_marshmallow_for_fab() -> None:
    """Apply monkey-patch if running on marshmallow >= 4.

    Safe to call on marshmallow 3 (no-op).
    """
    global _PATCHED  # noqa: PLW0603
    if _PATCHED or not _is_marshmallow_4():
        return

    _original_init_fields = Schema._init_fields

    def _patched_init_fields(self: Schema) -> None:
        max_retries = len(_FAB_FK_FIELD_NAMES) + 1
        for _ in range(max_retries):
            try:
                _original_init_fields(self)
                return
            except KeyError as exc:
                missing_field = str(exc).strip("'\"")
                if missing_field not in _FAB_FK_FIELD_NAMES:
                    raise
                logger.debug(
                    "marshmallow_compat: adding missing FAB field %r to %s",
                    missing_field,
                    type(self).__name__,
                )
                self._declared_fields[missing_field] = fields.Raw(
                    dump_default=None,
                    load_default=None,
                    load_only=True,
                )
        # Final attempt — let any remaining error propagate.
        _original_init_fields(self)

    Schema._init_fields = _patched_init_fields
    _PATCHED = True
    logger.debug("marshmallow_compat: patched Schema._init_fields for FAB")
