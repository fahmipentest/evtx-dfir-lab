#!/usr/bin/env python3
"""
evtx_parse.py - Ringkas isi file .evtx dan tampilkan event tertentu.

Contoh:
  python scripts/evtx_parse.py Security.evtx            # ringkasan Event ID
  python scripts/evtx_parse.py Security.evtx 4624 4625  # detail Event ID tertentu
"""
import sys
import collections
import xml.etree.ElementTree as ET

from Evtx.Evtx import Evtx

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)

    path = sys.argv[1]
    wanted = set(sys.argv[2:])
    counter = collections.Counter()

    with Evtx(path) as log:
        for rec in log.records():
            root = ET.fromstring(rec.xml())
            eid = root.find("e:System/e:EventID", NS).text
            counter[eid] += 1
            if wanted and eid not in wanted:
                continue
            if wanted:
                waktu = root.find("e:System/e:TimeCreated", NS).attrib["SystemTime"][:19]
                data = {
                    d.attrib.get("Name"): d.text
                    for d in root.findall("e:EventData/e:Data", NS)
                }
                print(waktu, eid, data)

    print("\nRingkasan Event ID:", dict(counter.most_common()))


if __name__ == "__main__":
    main()
