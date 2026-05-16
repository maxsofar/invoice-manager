# Invoice Manager

A local web app for managing clients, orders, and PDF invoices — built because the existing tools for this don't run well on Mac and most look terrible.

## Why I built it

I wanted to see how quickly I could put together something genuinely usable. The goal was clean UI, working PDF output, and Hebrew/English support — none of which the existing options handled well together.

## What it does

- Add and remove clients, searchable by name
- Create orders with dynamic line items (added client-side without page reloads)
- View order items per order
- Generate a PDF invoice per order, built server-side with custom fonts and a logo

## Stack

- **Backend** — Python, Flask
- **Database** — SQLite (via `database_setup.py`)
- **PDF generation** — ReportLab (server-side, custom fonts)
- **i18n** — Flask-Babel with Hebrew translations and RTL layout support
- **Frontend** — HTML/CSS, jQuery (AJAX for client/order operations)

## i18n / RTL

The app supports Hebrew and English. Language is selected via `?lang=he` or `?lang=en`. Templates detect the active locale and set `dir="rtl"` or `dir="ltr"` accordingly. Hebrew translations are in `messages.po`.

## Running locally

```bash
pip install -r requirements.txt
python database_setup.py   # creates the SQLite schema
python app.py              # starts on http://127.0.0.1:5000
```

## Project structure

```
app.py               # Flask app, routes, PDF generation
database_setup.py    # creates clients / orders / order_items tables
templates/
  index.html
  client_section.html
  order_add.html
  orders_section.html
fonts/               # fonts used in PDF output
translations/        # Flask-Babel i18n files (Hebrew)
requirements.txt
```

> **Note:** `database.db` is excluded from this repo — run `database_setup.py` to create a fresh one locally.
