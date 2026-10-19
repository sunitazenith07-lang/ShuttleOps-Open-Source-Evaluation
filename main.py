"""Command-line preview for ShuttleOps."""
from service import list_records, summary, filter_records

def main():
    rows=list_records()
    print("ShuttleOps — Student Starter")
    print(f"Loaded {len(rows)} trips")
    for row in rows:
        print(f"#{row.id} | {row.route_name} | {row.origin} -> {row.destination} | {row.status}")
    query=input("Search route/origin/destination (Enter to skip): ").strip()
    category=input("Category filter (Enter to skip): ").strip() or None
    status=input("Status filter (Enter to skip): ").strip() or None
    try:
        results=filter_records(rows,query,category,status)
    except ValueError as exc:
        print(f"Invalid filter: {exc}")
        return
    if not results:
        print("No trips match your filters.")
    else:
        for row in results:
            print(f"#{row.id} | {row.route_name} | {row.status} | seats {row.passengers}/{row.capacity}")
    print("Summary:",summary(rows))

if __name__=="__main__":
    main()
