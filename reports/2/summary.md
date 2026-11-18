# Perbandingan Cashier 1 dan Cashier 3

Perbandingan dilakukan pada `dataset/Cashier 1.bpmn` dan
`dataset/Cashier 3.bpmn` dengan empat strategi alignment. Kedua model berformat
BPMN, masing-masing berisi 19 node dan 21 flow.

## Ringkasan hasil

| Alignment | Identik | Sinonim | Makna berubah | Dihapus / ditambahkan | Operasi | Trace equivalent | Bisimulasi | Verdict |
|---|---:|---:|---:|---:|---:|---|---|---|
| `id` | 0 | 0 | 0 | 19 / 19 | 61 | Tidak | Tidak | `behavioral_change` |
| `name` | 3 | 2 | 3 | 11 / 11 | 52 | Tidak | Tidak | `semantic_and_behavioral_change` |
| `structure` | 10 | 1 | 4 | 4 / 4 | 23 | Tidak | Tidak | `semantic_and_behavioral_change` |
| `hybrid` | 11 | 2 | 5 | 1 / 1 | 13 | Tidak | Tidak | `semantic_and_behavioral_change` |

Jumlah operasi mencakup perubahan node, flow, dan data.

## Interpretasi

- `id` tidak menemukan ID bersama pada pasangan ini, sehingga melaporkan
  seluruh 19 node sebagai dihapus dan 19 sebagai ditambahkan. Ini hasil yang
  diharapkan dari mode ID yang ketat, bukan bukti bahwa seluruh proses benar-benar
  diganti.
- `name` memasangkan 8 node, `structure` memasangkan 15, dan `hybrid`
  memasangkan 18. Pada pasangan ini, `hybrid` menghasilkan unmatched serta
  jumlah operasi paling sedikit.
- Trace equivalence dan branching bisimulation menyatakan **tidak ekuivalen**
  untuk keempat mode. Jumlah dan klasifikasi operasi tetap dipengaruhi strategi
  alignment, sehingga periksa edit script sebelum menafsirkan unmatched sebagai
  perubahan nyata.
- Hybrid memasangkan `Enters Down Payment information` dengan
  `Enters the receipt number` karena keduanya punya konteks tetangga yang sama
  dan memiliki token label yang sama. `Saves the Down Payment information` dan
  `Prints the receipt` tetap unmatched karena tidak memiliki bukti leksikal
  bersama; algoritma tidak memaksakan pasangan hanya berdasarkan posisi.

## Laporan terperinci

- [Alignment ID](cashier_1_vs_3_id.md) · [JSON](cashier_1_vs_3_id.json)
- [Alignment Name](cashier_1_vs_3_name.md) · [JSON](cashier_1_vs_3_name.json)
- [Alignment Structure](cashier_1_vs_3_structure.md) · [JSON](cashier_1_vs_3_structure.json)
- [Alignment Hybrid](cashier_1_vs_3_hybrid.md) · [JSON](cashier_1_vs_3_hybrid.json)

Laporan perbandingan Cashier 1 vs Cashier 2 tetap tersedia dengan nama
`cashier_1_vs_2_*`; ringkasan ini sekarang merujuk ke Cashier 1 vs Cashier 3.
