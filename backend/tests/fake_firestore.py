"""An in-memory stand-in for the parts of Firestore our routes use."""
import copy
import uuid
from collections import defaultdict

from google.api_core.exceptions import Conflict, NotFound


class FakeSnapshot:
    def __init__(self, doc_id, data):
        self.id = doc_id
        self._data = data

    @property
    def exists(self):
        return self._data is not None

    def to_dict(self):
        return copy.deepcopy(self._data)


class FakeDocument:
    def __init__(self, store, doc_id):
        self._store = store
        self.id = doc_id

    def get(self):
        return FakeSnapshot(self.id, self._store.get(self.id))

    def set(self, data):
        self._store[self.id] = copy.deepcopy(data)

    def create(self, data):
        if self.id in self._store:
            raise Conflict("Document already exists")
        self.set(data)

    def update(self, changes):
        if self.id not in self._store:
            raise NotFound("No document to update")
        self._store[self.id].update(copy.deepcopy(changes))


class FakeQuery:
    def __init__(self, store, field_filter=None):
        self._store = store
        self._filter = field_filter

    def where(self, *, filter):
        assert filter.op_string == "==", "the fake only supports == filters"
        return FakeQuery(self._store, filter)

    def stream(self):
        for doc_id, data in self._store.items():
            if self._filter is None or data.get(self._filter.field_path) == self._filter.value:
                yield FakeSnapshot(doc_id, data)


class FakeCollection(FakeQuery):
    def document(self, doc_id=None):
        return FakeDocument(self._store, doc_id or uuid.uuid4().hex)


class FakeFirestore:
    def __init__(self):
        self._collections = defaultdict(dict)

    def collection(self, name):
        return FakeCollection(self._collections[name])
