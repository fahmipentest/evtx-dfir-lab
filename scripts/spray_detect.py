#!/usr/bin/env python3
"""
spray_detect.py - Deteksi pola password spray / brute force dari log EVTX.

Logika: kelompokkan percobaan login GAGAL berdasarkan IP sumber, lalu hitung
berapa username berbeda yang dicoba dari IP yang sama.

Event yang dipakai:
  4625  Logon gagal (Security)
  4771  Kerberos pre-authentication gagal (Domain Controller)
  4768  Permintaan TGT; Status selain 0x0 dianggap gagal

Contoh:
  python scripts/spray_detect.py kerberos_pwd_spray_4771.evtx
  python scripts/spray_detect.py Security.evtx --threshold 5
"""
import argparse
import collections
import xml.etree.ElementTree as ET

from Evtx.Evtx import Evtx

NS = {"e": "http://schemas.microsoft.com/win/2004/08/events/event"}


def main():
    ap = argparse.ArgumentParser(description="Deteksi password spray dari EVTX")
    ap.add_argument("evtx")
    ap.add_argument("--threshold", type=int, default=3,
                    help="minimal jumlah username berbeda dari 1 IP (default 3)")
    args = ap.parse_args()

    per_ip = collections.defaultdict(lambda: {"users": collections.Counter(), "n": 0})

    with Evtx(args.evtx) as log:
        for rec in log.records():
            root = ET.fromstring(rec.xml())
            eid = root.find("e:System/e:EventID", NS).text
            if eid not in ("4625", "4771", "4768"):
                continue
            d = {x.attrib.get("Name"): x.text
                 for x in root.findall("e:EventData/e:Data", NS)}
            if eid == "4768" and int(d.get("Status") or "0x0", 16) == 0:
                continue  # TGT sukses (Status ditulis 0x0 atau 0x00000000)
            ip = (d.get("IpAddress") or "-").replace("::ffff:", "")
            user = d.get("TargetUserName") or "?"
            per_ip[ip]["users"][user] += 1
            per_ip[ip]["n"] += 1

    if not per_ip:
        print("Tidak ada percobaan login gagal ditemukan.")
        return

    print(f"{'IP sumber':<20}{'gagal':>7}{'user unik':>11}  status")
    for ip, v in sorted(per_ip.items(), key=lambda kv: -len(kv[1]["users"])):
        uniq = len(v["users"])
        flag = "<< DICURIGAI (spray)" if uniq >= args.threshold else ""
        print(f"{ip:<20}{v['n']:>7}{uniq:>11}  {flag}")
        if flag:
            print("   user dicoba:", ", ".join(sorted(v["users"])))


if __name__ == "__main__":
    main()
