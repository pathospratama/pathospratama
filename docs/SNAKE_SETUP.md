# 🐍 Contribution Snake Setup

Animasi ini mengambil contribution graph GitHub `pathospratama`, mengubahnya menjadi permainan snake, dan menghasilkan SVG animasi untuk dipakai langsung pada profile README.

## File

- `.github/workflows/snake.yml` — workflow generator.
- `README.md` — menampilkan snake dalam mode dark/light.
- `preview.html` — preview aset repository secara lokal.

## Cara kerja

1. GitHub Actions menjalankan `Platane/snk/svg-only@v3`.
2. Workflow membaca contribution graph akun `pathospratama`.
3. Dua SVG dibuat:
   - `github-contribution-grid-snake.svg`
   - `github-contribution-grid-snake-dark.svg`
4. SVG dipublish ke branch `output`.
5. README mengambil SVG dari branch `output` lewat `raw.githubusercontent.com`.

## Menjalankan

Commit dan push:

```bash
git add .github/workflows/snake.yml README.md preview.html docs/SNAKE_SETUP.md
git commit -m "feat: add contribution snake animation"
git push origin main
```

Lalu buka tab **Actions** di repository dan jalankan **Generate Contribution Snake** dengan `Run workflow`.

## Permission

Repository harus mengizinkan workflow menulis isi repository:

`Settings → Actions → General → Workflow permissions → Read and write permissions`

Jika repository profile menggunakan default permission yang berbeda, aktifkan izin write tersebut sebelum menjalankan workflow.

## Output URL

```text
https://raw.githubusercontent.com/pathospratama/pathospratama/output/github-contribution-grid-snake.svg
https://raw.githubusercontent.com/pathospratama/pathospratama/output/github-contribution-grid-snake-dark.svg
```

## Kustomisasi

Warna snake saat ini memakai identitas visual Pathos:

```text
Lavender : #AA9BEF
Mint     : #7EE7C7
Amber    : #F5C77E
Dark     : #0D1117
Muted    : #8B949E
```

Untuk mengubah warna snake, edit `color_snake` pada `snake.yml`.
