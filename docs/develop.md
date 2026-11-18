# Roadmap Pengembangan & Evaluasi `bpmndiff`

Dokumen ini merangkum daftar pengembangan, standarisasi arsitektur, dan kerangka evaluasi kuantitatif untuk meningkatkan `bpmndiff` dari prototipe fungsional menjadi sistem perbandingan model proses yang terukur dan tervalidasi.

---

## 1. Standarisasi Taksonomi & Kontrak Output
Memastikan hasil deteksi perubahan memiliki standar baku yang konsisten dan dapat divalidasi secara otomatis.

- [x] **Taksonomi & JSON Schema v1 (`docs/changes.md`, `schema/change-v1.json`)**
  - Mendokumentasikan daftar resmi jenis perubahan yang didukung beserta struktur JSON-nya agar seluruh output mematuhi kontrak skema baku.
- [x] **Output 2 Layer (`change` + `evidence`)**
  - **Layer 1 (`change`)**: Mendeskripsikan jenis dan detail perubahan (misalnya `MOVE_LANE`, `RENAME_NODE`, elemen asal/tujuan).
  - **Layer 2 (`evidence`)**: Menyertakan bukti pendukung keputusan alignment (misalnya skor kemiripan leksikal, kecocokan tetangga struktural, atau koordinat geometri BPMN DI).
- [x] **Invariant Checker Aktif**
  - Menjalankan pemeriksaan konsistensi logis otomatis setiap kali proses *diff* selesai (memastikan tidak ada node yang terdeteksi ganda seperti `DELETE` sekaligus `RENAME`, memvalidasi integritas alignment, dan memastikan output sesuai dengan `schema/change-v1.json`).

---

## 2. Perluasan Operasi Diff & Modularisasi Mode
Memisahkan strategi pencocokan agar dapat diuji secara adil (*ablation study*) serta memperkaya jenis perubahan struktural yang terdeteksi.

- [x] **4 Mode Alignment via Parameter & CLI (`--alignment-mode id | name | structure | hybrid`)**
  - `id`: Pencocokan hanya berdasarkan kesamaan UUID/ID XML.
  - `name`: Pencocokan hanya berdasarkan kemiripan teks/label.
  - `structure`: Pencocokan hanya berdasarkan topologi graf dan konteks tetangga (*structural context*).
  - `hybrid`: Gabungan berjenjang (*tiered alignment*) yang memadukan seluruh sinyal.

---

## 3. Synthetic Dataset Generator & Regression Test
Membangun dataset uji sintetis beserta *ground truth* otomatis serta mengunci kasus uji regresi utama.

- [ ] **Generator 30 Pasangan Mutasi (`k = 1, 2, 4`)**
  - Menyuntikkan $k$ mutasi terkontrol ($k=1$ perubahan tunggal, $k=2$ perubahan ganda, $k=4$ perubahan kompleks) ke model referensi sekaligus menghasilkan kunci jawaban dalam format JSON v1.
  - Setiap variasi diuji dalam 2 skenario: **ID dipertahankan** vs **ID diganti total** (mensimulasikan kondisi *re-export* diagram).
- [ ] **10 Pasangan *Noise***
  - Pasangan diagram yang secara semantik dan struktural identik, namun diberi gangguan (*noise*) seperti perubahan UUID total, pergeseran koordinat X/Y, atau variasi spasi/kapitalisasi untuk menguji ketahanan terhadap *false positive*.
- [x] **Regression Test Kasus `Cashier` ("Invisible Task")**
  - Mengunci perbandingan `Cashier 1.bpmn` vs `Cashier 2.bpmn` sebagai pengujian otomatis untuk memastikan pasangan *Invisible Task* terdeteksi bersih sebagai `RENAME_NODE` (bukan `DELETE` + `INSERT` palsu).

---

## 4. Benchmarking, Metrik Evaluasi, & Analisis Kegagalan
Melakukan evaluasi ilmiah secara kuantitatif terhadap sistem yang dibangun maupun pustaka pembanding.

- [ ] **Baseline Pembanding (`bpmn-js-differ`)**
  - Menjalankan `bpmn-js-differ` pada 30 pasangan dataset yang sama sebagai tolok ukur (*benchmark*), khususnya pada skenario pergantian ID.
- [ ] **Evaluation Harness (`results/pilot.csv`)**
  - Skrip otomatis untuk membandingkan hasil deteksi sistem dan baseline terhadap *ground truth*, lalu menghitung metrik **Precision**, **Recall**, dan **F1-Score** yang dirinci **per jenis perubahan** dan **per mode** (`id`, `name`, `structure`, `hybrid`).
- [ ] **Analisis Kegagalan (*Error Analysis*)**
  - Mengidentifikasi **3 pola kegagalan paling sering** yang terjadi pada sistem, dilengkapi **1 contoh kasus diagram** untuk masing-masing pola kegagalan.

---

## 5. Kolaborasi & Version Control

- [ ] **Repositori GitLab**
  - Mengelola seluruh kode sumber, dokumentasi taksonomi, skema JSON, generator dataset, skrip evaluasi, dan hasil CSV secara terpusat di repositori GitLab lab untuk memudahkan pemantauan dan reproduksibilitas.

---

## Urutan Pengerjaan (Berdasarkan Dependensi)

1. **Tahap 1 — Fondasi & Skema**: Buat `docs/changes.md` & `schema/change-v1.json` $\rightarrow$ refaktor output ke format 2 layer (`change` + `evidence`) $\rightarrow$ aktifkan *invariant checker*.
2. **Tahap 2 — Fitur Inti & CLI**: Implementasikan deteksi `MOVE_LANE`, `REORDER`, dan `GATEWAY_TYPE_CHANGE` $\rightarrow$ tambahkan opsi CLI `--alignment-mode id|name|structure|hybrid` $\rightarrow$ pastikan *regression test* `Cashier` lulus.
3. **Tahap 3 — Dataset & Baseline**: Bangun generator 30 pasangan mutasi + 10 pasangan *noise* $\rightarrow$ jalankan `bpmn-js-differ` pada dataset yang sama.
4. **Tahap 4 — Evaluasi & Analisis**: Bangun *evaluation harness* untuk menghasilkan `results/pilot.csv` (Precision, Recall, F1) $\rightarrow$ dokumentasikan 3 pola kegagalan teratas beserta contoh diagramnya $\rightarrow$ *push* seluruh progres ke GitLab.