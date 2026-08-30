# Flashcard PDF Generator

A Python tool to generate printable, double-sided flashcards from a CSV file. It automatically aligns front and rear card sides for double-sided (duplex) printing, wraps and scales text, and renders cutting guidelines.

## Features

- **Double-Sided Duplex Alignment**: Automatically mirrors card positions on reverse pages so that front and back match when printed duplex (flip on long edge).
- **Auto-Fit & Text Scaling**: Dynamically wraps text and scales font sizes so cards with longer text do not overflow.
- **Smart Grid Calculation**: Automatically computes the best grid layout (`rows × cols`) for standard card counts (2, 4, 6, 8, 9, 10, 12, etc.), with option to override.
- **Cutting Guides**: Draws dashed guidelines, solid borders, or crop marks for easy scissor or paper cutter trimming.
- **Multiple Page Sizes**: Supports `letter`, `a4`, and `legal`.

## Installation

1. Clone or download this repository.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## CSV Format

The CSV file should contain two columns (Column 1 = Front text, Column 2 = Rear text):

```csv
Front,Rear
Hello,Hola
Goodbye,Adiós
Thank you,Gracias
Please,Por favor
```

- Headers (e.g., `Front,Rear` or `Question,Answer`) are automatically detected and skipped.
- Multi-line text and quoted entries are supported.

## Usage

```bash
python generate_flashcards.py <csv_path> <cards_per_page> <output_pdf> [options]
```

### Positional Arguments

- `csv_path`: Path to the CSV file containing flashcard data.
- `cards_per_page`: Number of cards per page (e.g., `4`, `8`, `10`).
- `output_pdf`: Path to the destination PDF file.

### Options

| Option | Default | Description |
| :--- | :--- | :--- |
| `--page-size` | `letter` | Paper size: `letter`, `a4`, or `legal`. |
| `--grid` | *auto* | Custom grid dimensions as `ROWSxCOLS` (e.g. `--grid 4x2`). |
| `--margin` | `0.5` | Page margins in inches. |
| `--border-style` | `dashed` | Border style: `dashed`, `solid`, `crop-marks`, or `none`. |
| `--flip` | `long-edge` | Duplex flip alignment: `long-edge` (portrait), `short-edge`, or `none`. |
| `--font-size` | `18.0` | Maximum font size in points. |
| `--has-header` / `--no-has-header` | *auto* | Explicitly declare whether CSV has a header row. |

### Examples

Generate a letter-sized PDF with 8 flashcards per page:
```bash
python generate_flashcards.py sample_cards.csv 8 flashcards.pdf
```

Generate an A4-sized PDF with solid borders and a 3x3 grid (9 cards):
```bash
python generate_flashcards.py vocab.csv 9 cards_a4.pdf --page-size a4 --border-style solid
```

## Running Tests

```bash
pytest
```
