#!/usr/bin/env python3
"""show_inverter_data.py — Display all data from the Sungrow inverter."""

from sungrowinverter import SungrowInverter, print_all_data


def main():
    """Create client and display all available data."""
    inverter = SungrowInverter(
        host="modbusSungrow.fritz.box",
        port=502,
        unit_id=1
    )
    print_all_data(inverter)


if __name__ == "__main__":
    main()