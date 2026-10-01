from logistics_redactor import ShipmentEvent, archive_record


def main() -> None:
    event = ShipmentEvent("SHP-1042", "delivered", "Lin Wei", "+86-13800000000", "18 River Road")
    print(archive_record(event))


if __name__ == "__main__":
    main()
