# EVTX DFIR Lab

Lab belajar **forensik log Windows (EVTX)** di Kali Linux: membaca file `.evtx`, mengenali jejak serangan, dan membandingkan analisis manual dengan deteksi otomatis (Chainsaw + Sigma).

> Project ini ditujukan untuk **pembelajaran dan analisis defensif** (DFIR, blue team, persiapan sertifikasi) memakai sampel publik atau log dari lab pribadi. Jangan menganalisis log milik pihak lain tanpa izin.
> <img width="1004" height="422" alt="evtx-env" src="https://github.com/user-attachments/assets/63da9665-bd06-4187-ac7f-d941540fa148" />


## Daftar isi

1. [Apa itu EVTX dan kenapa penting](#1-apa-itu-evtx-dan-kenapa-penting)
2. [Isi project](#2-isi-project)
3. [Cara project ini dibuat](#3-cara-project-ini-dibuat)
4. [Instalasi cepat](#4-instalasi-cepat)
5. [Cara penggunaan](#5-cara-penggunaan)
6. [Studi kasus](#6-studi-kasus)
7. [Referensi Event ID](#7-referensi-event-id)
8. [Keterbatasan dan masalah yang diketahui](#8-keterbatasan-dan-masalah-yang-diketahui)
9. [Bahan belajar lanjutan](#9-bahan-belajar-lanjutan)
10. [Kredit dan lisensi](#10-kredit-dan-lisensi)

---

## 1. Apa itu EVTX dan kenapa penting

**EVTX** adalah format file log bawaan Windows (Vista ke atas). Setiap aktivitas penting dicatat sebagai *event* dengan nomor **Event ID**: login berhasil atau gagal, proses baru, service baru, eksekusi PowerShell, dan sebagainya. File-nya ada di `C:\Windows\System32\winevt\Logs\` (`Security.evtx`, `System.evtx`, `Microsoft-Windows-Sysmon%4Operational.evtx`, dll).

Dalam investigasi insiden, log ini menjawab pertanyaan seperti:

- Siapa yang mencoba login, dari IP mana, berhasil atau tidak?
- Program apa yang dijalankan, oleh siapa, dengan parameter apa?
- Apakah ada service atau scheduled task yang dipasang attacker untuk persistence?
- Apakah ada yang menghapus log untuk menutupi jejak? (Event ID 1102)

Project ini mengajarkan cara membaca log tersebut dari awal, dengan dua pendekatan:

| Pendekatan | Tool | Kelebihan | Kekurangan |
|---|---|---|---|
| **Manual** | `python-evtx` + script Python | Paham struktur data, bisa dibuat logika sendiri (misalnya menghitung pola) | Lambat untuk file besar |
| **Otomatis** | Chainsaw + aturan Sigma | Cepat, langsung memberi nama teknik serangan | Hanya menilai pola yang sudah ada aturannya |

Kedua pendekatan saling melengkapi (lihat studi kasus 1).

## 2. Isi project

```
evtx-dfir-lab/
├── README.md              Dokumentasi ini
├── setup.sh               Pemasangan otomatis seluruh lab
├── requirements.txt       Dependensi Python (python-evtx, hexdump)
├── .gitignore             Mengecualikan samples/, tools/, output/, .venv/
└── scripts/
    ├── evtx_parse.py      Ringkasan Event ID + tampilkan event tertentu
    └── spray_detect.py    Deteksi password spray dari login gagal
```

Folder berikut dibuat oleh `setup.sh` dan **tidak** ikut di-commit:

```
.venv/        Virtual environment Python
samples/      Sampel EVTX (EVTX-ATTACK-SAMPLES)
tools/        Chainsaw dan aturan Sigma
output/       Tempat menyimpan hasil analisismu
```

## 3. Cara project ini dibuat

Bagian ini menjelaskan langkah demi langkah apa yang dilakukan `setup.sh`, supaya kamu paham dan bisa membangunnya manual.

### 3.1 Virtual environment Python

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install python-evtx hexdump
```

*Virtual environment* (venv) adalah folder Python terisolasi. Paket yang dipasang di dalamnya tidak mengganggu Python sistem Kali. Ini penting di Kali karena paket Python sistem dikelola `apt`.

- **python-evtx** (karya Willi Ballenthin): library parser EVTX murni Python.
- **hexdump**: dependensi pendukung.

Saat dipasang, python-evtx juga menyediakan command di folder `bin/` venv: `evtx_dump`, `evtx_dump_json`, `evtx_info`, `evtx_eid_record_numbers`, `evtx_extract_record`, `evtx_dump_chunk_slack`, dan lainnya.

### 3.2 Sampel serangan

```bash
git clone --depth 1 https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES.git samples/EVTX-ATTACK-SAMPLES
```

Repo ini berisi ratusan file EVTX dari serangan yang dijalankan di lab, dikelompokkan per taktik MITRE ATT&CK. `--depth 1` hanya mengambil versi terbaru supaya unduhan lebih kecil.

### 3.3 Chainsaw dan aturan Sigma

```bash
curl -L -o chainsaw.tgz https://github.com/WithSecureLabs/chainsaw/releases/download/v2.17.1/chainsaw_x86_64-unknown-linux-gnu.tar.gz
tar xzf chainsaw.tgz -C tools
git clone --depth 1 https://github.com/SigmaHQ/sigma.git tools/sigma
```

- **Chainsaw** membaca EVTX dengan cepat dan mencocokkannya dengan aturan.
- **Sigma** adalah kumpulan aturan deteksi yang ditulis dalam format YAML generik, dipelihara komunitas.
- File *mapping* Chainsaw (`tools/chainsaw/mappings/sigma-event-logs-all.yml`) menerjemahkan nama field di aturan Sigma ke nama field di EVTX.

`setup.sh` menjalankan semua langkah ini otomatis dan memilih file Chainsaw sesuai arsitektur CPU (x86_64 atau aarch64).

## 4. Instalasi cepat

```bash
git clone https://github.com/fahmipentest/evtx-dfir-lab.git
cd evtx-dfir-lab
./setup.sh
source .venv/bin/activate
```

Kebutuhan: Linux (diuji di lingkungan Ubuntu 24 dengan Python 3.12), `git`, `curl`, dan koneksi internet.

## 5. Cara penggunaan

Semua perintah dijalankan dari root project dengan venv aktif.

Biar singkat, simpan lokasi sampel di variabel:

```bash
S="samples/EVTX-ATTACK-SAMPLES"
```

### 5.1 Alur kerja yang disarankan

```
1. Ringkasan  ->  2. Lihat detail  ->  3. Deteksi otomatis  ->  4. Analisis manual
```

### 5.2 `evtx_parse.py`: ringkasan dan detail

```bash
# Ringkasan: ada Event ID apa saja dan berapa banyak
python scripts/evtx_parse.py "$S/Credential Access/kerberos_pwd_spray_4771.evtx"
# -> Ringkasan Event ID: {'4768': 9, '4771': 2, '1102': 1}

# Detail Event ID tertentu (bisa lebih dari satu)
python scripts/evtx_parse.py "$S/Credential Access/kerberos_pwd_spray_4771.evtx" 4771 4768
```

Selalu mulai dari ringkasan untuk melihat isi log sebelum menggali detail.

### 5.3 `spray_detect.py`: deteksi password spray

```bash
python scripts/spray_detect.py "$S/Credential Access/kerberos_pwd_spray_4771.evtx"
python scripts/spray_detect.py Security.evtx --threshold 5
```

Cara kerjanya: mengelompokkan login gagal (4625, 4771, dan 4768 dengan Status bukan 0x0) berdasarkan IP sumber, lalu menghitung berapa username berbeda yang dicoba dari IP yang sama. Jika jumlahnya mencapai `--threshold` (default 3), IP itu ditandai.

Contoh keluaran pada sampel:

```
IP sumber            gagal  user unik  status
172.16.66.1              9          9  << DICURIGAI (spray)
   user dicoba: Administrator, HD01, HD02, admin, admin02, backdoor, bob, svc-01, svc-02
```

### 5.4 Chainsaw: deteksi otomatis dengan Sigma

```bash
tools/chainsaw/chainsaw hunt "$S/Credential Access/sysmon_10_1_memdump_comsvcs_minidump.evtx" \
  -s tools/sigma/rules/windows \
  --mapping tools/chainsaw/mappings/sigma-event-logs-all.yml \
  --skip-errors
```

| Opsi | Fungsi |
|---|---|
| `hunt` | Mode deteksi memakai aturan |
| `-s` | Folder aturan Sigma |
| `--mapping` | Peta field Sigma ke field EVTX |
| `--skip-errors` | Lanjut walau ada record rusak |
| `-q` | Sembunyikan banner |
| `--json` | Keluaran JSON, bisa diolah script |

Untuk daftar ringkas nama deteksi saja:

```bash
tools/chainsaw/chainsaw hunt "$S/Credential Access/sysmon_10_1_memdump_comsvcs_minidump.evtx" \
  -s tools/sigma/rules/windows \
  --mapping tools/chainsaw/mappings/sigma-event-logs-all.yml \
  --skip-errors -q --json 2>/dev/null | python3 -c "
import json,sys
for d in json.load(sys.stdin): print(' -', d['name'], '['+d['level']+']')"
```

### 5.5 Chainsaw: pencarian

```bash
# Berdasarkan Event ID (sintaks Tau)
tools/chainsaw/chainsaw search -q -t 'Event.System.EventID: =4771' file.evtx --json

# Berdasarkan kata, tanpa membedakan huruf besar/kecil
tools/chainsaw/chainsaw search -q -i "backdoor" file.evtx
```

### 5.6 Command bawaan python-evtx

Dengan venv aktif tersedia `evtx_dump`, `evtx_dump_json`, `evtx_eid_record_numbers`, `evtx_extract_record`, `evtx_dump_chunk_slack`, dan lainnya. Contoh:

```bash
evtx_dump file.evtx > file.xml        # semua record ke XML
evtx_dump_json file.evtx > file.json  # ke JSON
```

Lihat [bagian 8](#8-keterbatasan-dan-masalah-yang-diketahui): `evtx_info` bermasalah di instalasi yang saya uji.

## 6. Studi kasus

### Kasus 1: Kerberos password spray

**Sampel:** `Credential Access/kerberos_pwd_spray_4771.evtx`

**Ringkasan log:** 9 event 4768, 2 event 4771, 1 event 1102.

**Temuan:**

| Temuan | Arti |
|---|---|
| Semua percobaan dari `172.16.66.1` dengan 9 username berbeda | Satu sumber mencoba banyak akun: pola **spray** |
| 4768 `Status 0x6` (7 kali) | Username tidak ada di domain (enumerasi user) |
| 4771 `Status 0x18` untuk `Administrator` dan `backdoor` | Akun ada, password salah |
| 4768 `Status 0x0` untuk `normal` | TGT berhasil diterbitkan (login sah) |
| Event 1102 | Log pernah dihapus, temuan tersendiri |
| Semua event dalam satu detik | Dikerjakan tool otomatis |

**Pelajaran penting:** menjalankan `chainsaw hunt` dengan Sigma pada sampel ini menghasilkan **0 deteksi**. Aturan Sigma menilai event satu per satu, sedangkan spray baru terlihat setelah banyak event dihitung bersama. Karena itu `spray_detect.py` dibuat. Tool otomatis tidak menggantikan analisis manual.

### Kasus 2: Dump memori proses lewat comsvcs.dll

**Sampel:** `Credential Access/sysmon_10_1_memdump_comsvcs_minidump.evtx`

**Urutan kejadian (Sysmon):**

| Waktu | EID | Isi |
|---|---|---|
| 12:54:07 | 1 | `cscript c:\ProgramData\memdump.vbs notepad.exe` (parent `cmd.exe`) |
| 12:54:08 | 1 | `rundll32 C:\windows\system32\comsvcs.dll, MiniDump 4868 C:\Windows\System32\notepad.bin full` (parent `WmiPrvSE.exe`) |
| 12:54:08 | 11 | File dump dibuat |
| 12:54:08 | 10 | `rundll32.exe` membuka `notepad.exe` dengan akses `0x1fffff` |

**Deteksi Chainsaw + Sigma (5 temuan):**

- Process Memory Dump Via Comsvcs.DLL (high)
- Suspicious WmiPrvSE Child Process (high)
- Potentially Suspicious Rundll32 Activity (medium)
- WmiPrvSE Spawned A Process (medium)
- Uncommon Process Access Rights For Target Image (low)

**Pelajaran:**

- `rundll32 ... comsvcs.dll, MiniDump` adalah teknik memakai program bawaan Windows (*LOLBin*) untuk dump memori. Pada serangan nyata targetnya biasanya `lsass.exe` untuk mengambil kredensial. Sampel ini memakai `notepad.exe` sebagai pengganti aman.
- Parent `WmiPrvSE.exe` menunjukkan perintah dijalankan lewat WMI (kemungkinan remote).
- `GrantedAccess 0x1fffff` adalah akses penuh ke proses target.
- Script di `C:\ProgramData` (folder yang bisa ditulis user biasa) sering dipakai attacker.

### Latihan mandiri

| File | Yang dipelajari |
|---|---|
| `Lateral Movement/LM_5145_Remote_FileCopy.evtx` | Salin file lewat SMB (EID 5145) |
| `Lateral Movement/LM_PowershellRemoting_sysmon_1_wsmprovhost.evtx` | PowerShell remoting |
| `Credential Access/CA_DCSync_4662.evtx` | Serangan DCSync (EID 4662) |
| `Credential Access/sysmon_10_lsass_mimikatz_sekurlsa_logonpasswords.evtx` | Mimikatz mengakses LSASS |
| `Credential Access/Powershell_4104_MiniDumpWriteDump_Lsass.evtx` | Dump LSASS lewat PowerShell |

Untuk tiap file: ringkasan, lalu detail Event ID yang muncul, lalu `chainsaw hunt`, lalu tulis temuanmu sendiri di `output/`.

## 7. Referensi Event ID

| Log | Event ID | Arti |
|---|---|---|
| Security | 4624 | Logon sukses |
| Security | 4625 | Logon gagal |
| Security | 4688 | Proses baru dibuat |
| Security | 4698 | Scheduled task dibuat |
| Security | 4662 | Operasi pada objek AD (dipakai deteksi DCSync) |
| Security | 4768 | Permintaan TGT Kerberos |
| Security | 4771 | Pre-authentication Kerberos gagal |
| Security | 5145 | Akses share jaringan |
| Security | 1102 | Log Security dihapus |
| System | 7045 | Service baru terpasang |
| PowerShell/Operational | 4104 | Script block PowerShell |
| Sysmon/Operational | 1 | Proses dibuat |
| Sysmon/Operational | 3 | Koneksi jaringan |
| Sysmon/Operational | 10 | Akses ke proses lain |
| Sysmon/Operational | 11 | File dibuat |

Kode status Kerberos yang sering muncul: `0x6` (user tidak ditemukan), `0x18` (password salah), `0x0` (sukses).

## 8. Keterbatasan dan masalah yang diketahui

- **Hanya format `.evtx`.** python-evtx tidak membaca `.evt` (log XP lama), `.etl`, MFT, registry hive, prefetch, atau memory dump. Chainsaw mendukung beberapa artefak lain, cek dengan `chainsaw hunt --help`.
- **`evtx_info` error** `ModuleNotFoundError: No module named 'scripts'` pada python-evtx 0.8.1 di lingkungan yang saya uji (Python 3.12). Solusinya: pakai script di folder `scripts/` yang memanggil library `Evtx` langsung.
- **python-evtx lambat** untuk file ratusan MB. Untuk file besar pakai Chainsaw.
- **Sigma hanya menilai event tunggal.** Pola yang butuh agregasi (spray, brute force) harus dianalisis sendiri.
- **Sampel bersifat lab.** Log produksi jauh lebih bising, jadi hasil deteksi bisa menghasilkan banyak *false positive*.
- Versi Chainsaw dikunci di `v2.17.1` pada `setup.sh`. Ubah variabel `CHAINSAW_VER` untuk versi lain.

## 9. Bahan belajar lanjutan

- Format EVTX dan Event ID: dokumentasi Microsoft tentang Windows security auditing.
- [MITRE ATT&CK](https://attack.mitre.org/) untuk memetakan temuan ke taktik dan teknik.
- Tool lain untuk EVTX: Hayabusa, EvtxECmd (Eric Zimmerman).
- Artefak lain yang bisa dijadikan project lanjutan: analisis MFT (MFTECmd), memory forensics (Volatility 3), registry (RegRipper), prefetch (PECmd).

## 10. Kredit dan lisensi

Project ini hanya berisi script dan dokumentasi. Semua komponen lain diunduh dari sumber aslinya dan memiliki lisensi masing-masing, jadi periksa sebelum membagikan ulang:

- [python-evtx](https://github.com/williballenthin/python-evtx) oleh Willi Ballenthin
- [EVTX-ATTACK-SAMPLES](https://github.com/sbousseaden/EVTX-ATTACK-SAMPLES) oleh Samir Bousseaden
- [Chainsaw](https://github.com/WithSecureLabs/chainsaw) oleh WithSecure
- [Sigma](https://github.com/SigmaHQ/sigma) oleh SigmaHQ dan komunitas

Folder `samples/` dan `tools/` sengaja masuk `.gitignore` supaya tidak ikut ter-upload.

Dibuat oleh [fahmipentest](https://github.com/fahmipentest) sebagai catatan belajar DFIR.
