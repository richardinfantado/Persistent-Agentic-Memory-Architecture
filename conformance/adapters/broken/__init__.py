"""Deliberately defective adapters.

Each adapter here violates ONE specific PAMSPEC property. The
conformance harness must FAIL that adapter on the designated
suite case. If the harness passes a broken adapter that violates
a property the suite is meant to test, the suite is not actually
testing that property and the harness has a blind spot.

Do not use these in production. They exist to prove the harness
catches what it claims to catch.

Naming convention:
  BrokenXxxxAdapter — violates property Xxxxx.
  Each class documents:
   - The property it violates.
   - The suite case that MUST fail against it.
   - The expected failure mode (assertion or error mismatch).
"""

from .broken_scope import BrokenIgnoresScopeAdapter
from .broken_versioning import BrokenSilentOverwriteAdapter
from .broken_versioning import BrokenNonMonotonicSequenceAdapter
from .broken_versioning import BrokenAcceptsStaleExpectedVersionAdapter
from .broken_idempotency import BrokenReusesIdempotencyKeyAdapter
from .broken_tombstone import BrokenReadsDeletedObjectAdapter
from .broken_history import BrokenLosesUnknownExtensionFieldsAdapter

__all__ = [
    "BrokenIgnoresScopeAdapter",
    "BrokenSilentOverwriteAdapter",
    "BrokenNonMonotonicSequenceAdapter",
    "BrokenAcceptsStaleExpectedVersionAdapter",
    "BrokenReusesIdempotencyKeyAdapter",
    "BrokenReadsDeletedObjectAdapter",
    "BrokenLosesUnknownExtensionFieldsAdapter",
]
