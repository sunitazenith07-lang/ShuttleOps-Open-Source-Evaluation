"""Domain model for ShuttleOps."""
from dataclasses import asdict, dataclass
VALID_STATUSES = ["Scheduled", "Delayed", "Cancelled"]
VALID_CATEGORIES = ["Campus Loop", "Airport", "City", "Night"]
FIELD_NAMES = ["id", "route_name", "origin", "destination", "stops", "departure_time", "capacity", "passengers", "status", "category"]
@dataclass
class Trip:
    id: int
    route_name: str
    origin: str
    destination: str
    stops: list[str]
    departure_time: str
    capacity: int
    passengers: int
    status: str
    category: str
    @property
    def name(self): return str(self.route_name)
    @property
    def searchable_text(self):
        return " ".join(str(getattr(self, f, "")) for f in ["route_name", "origin", "destination", "stops", "category"])
    def to_dict(self): return asdict(self)
    def validate(self): return None
    @classmethod
    def from_dict(cls, row):
        if not isinstance(row, dict): raise ValueError("Each record must be a JSON object")
        missing = set(FIELD_NAMES).difference(row)
        if missing: raise ValueError("Missing fields: " + ", ".join(sorted(missing)))
        return cls(**{key: row[key] for key in FIELD_NAMES})
RECORD_CLASS = Trip
