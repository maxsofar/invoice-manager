from flask import Flask, render_template, request, send_file, jsonify, g
import sqlite3
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Image, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import os
from flask_babel import Babel, _



def get_locale():
    # You can use request.args, request.cookies, or any other method to determine the locale
    return request.args.get('lang', 'en')
app = Flask(__name__)
babel = Babel()
babel.init_app(app, locale_selector=get_locale)

# Configure available languages
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'he']

@app.before_request
def before_request():
    g.lang = get_locale()

# Define the path to the database file
db_path = os.path.join(os.path.dirname(__file__), 'database.db')

# Connect to the database
def get_db_connection():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

# Function to generate the PDF invoice
def generate_invoice_pdf(order, client, items):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,  # Set page size to A4
                            leftMargin=20, rightMargin=20, topMargin=20, bottomMargin=20)
    elements = []

    # Register fonts
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to the fonts
    font_path = os.path.join(base_dir, "fonts/Arial.ttf")
    pdfmetrics.registerFont(TTFont('Arial', font_path))

    font_path = os.path.join(base_dir, "fonts/Arial_Bold.ttf")
    pdfmetrics.registerFont(TTFont('Arial-Bold', font_path))

    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='RightAlign', alignment=2, fontName='Arial'))
    styles.add(ParagraphStyle(name='LeftAlign', alignment=0, fontName='Arial'))
    styles.add(ParagraphStyle(name='Bold', fontName='Arial-Bold'))

    # Add image with text on both sides
    image_path = os.path.join(base_dir, "images/logo.png")
    image = Image(image_path, width=100, height=100)

    left_text = Paragraph("Company Name<br/>Supplier No. XXXXX<br/>Authorized Dealer XXXXX", styles['LeftAlign'])
    right_text = Paragraph("Your Name<br/>Street Address, City<br/>Phone: PHONE_NUMBER", styles['RightAlign'])

    available_width = A4[0] - doc.leftMargin - doc.rightMargin
    header_table = Table([[left_text, image, right_text]],
                         colWidths=[available_width * 0.4, available_width * 0.2, available_width * 0.4])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOX', (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(header_table)

    elements.append(Spacer(1, 40))  # Adjust the height as needed

    # Header
    elements.append(Paragraph('Invoice', styles['Title']))

    # Client Information
    client_info = f"""
    <b>Client:</b> {client['name']}<br/>
    <b>Phone:</b> {client['phone_number']}<br/>
    """
    elements.append(Paragraph(client_info, styles['LeftAlign']))

    # Order Information
    order_info = f"""
    <b>Order ID:</b> {order['id']}<br/>
    <b>Date:</b> {order['date']}<br/>
    """
    elements.append(Paragraph(order_info, styles['LeftAlign']))

    # Table Data
    data = [
        ['Description', 'Quantity', 'Price per Unit', 'Total']
    ]

    total_price = 0
    for item in items:
        item_total = item['quantity'] * item['price_per_unit']
        total_price += item_total
        data.append([
            item['description'],
            item['quantity'],
            f"${item['price_per_unit']}",
            f"${item_total}"
        ])

    # Calculate tax and final price
    tax_rate = 0.18  # 18% tax rate
    tax = total_price * tax_rate
    final_price = total_price + tax


    # Add total price, tax, and final price to the table data
    data.append(['Total Price', '', '', f"${total_price:.2f}"])
    data.append(['Tax (18%)', '', '', f"${tax:.2f}"])
    data.append(['Final Price with Tax', '', '', f"${final_price:.2f}"])

    # Table Style with merged cells
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Arial-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('SPAN', (0, -3), (-2, -3)),  # Span the last three rows
        ('SPAN', (0, -2), (-2, -2)),
        ('SPAN', (0, -1), (-2, -1)),
        ('LINEBELOW', (0, -4), (-1, -4), 2, colors.black),  # Bold line
    ]))

    elements.append(table)

    # Build PDF
    doc.build(elements)
    buffer.seek(0)
    return buffer

@app.route('/')
def home():
    conn = get_db_connection()
    orders = conn.execute('''
        SELECT orders.*, clients.name AS client_name
        FROM orders
        JOIN clients ON orders.client_id = clients.id
    ''').fetchall()
    clients = conn.execute('SELECT * FROM clients').fetchall()
    conn.close()
    return render_template('index.html', clients=clients, orders=orders)

@app.route('/add_client', methods=['POST'])
def add_client():
    name = request.form['name']
    phone_number = request.form['phone_number']

    conn = get_db_connection()
    conn.execute('INSERT INTO clients (name, phone_number) VALUES (?, ?)', (name, phone_number))
    conn.commit()
    conn.close()

    return jsonify({"success": True, "message": "Client added successfully"})

@app.route('/remove_client', methods=['POST'])
def remove_client():
    client_id = request.form['client_id']

    conn = get_db_connection()
    conn.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    conn.commit()
    conn.close()
    return "Client removed successfully! <a href='/'>Back to home</a>"

@app.route('/search_clients', methods=['GET'])
def search_clients():
    query = request.args.get('query')
    conn = get_db_connection()
    clients = conn.execute("SELECT id, name FROM clients WHERE id LIKE ? OR name LIKE ?", ('%' + query + '%', '%' + query + '%')).fetchall()
    conn.close()
    results = ''.join([f'<div class="client-result" data-client-id="{client["id"]}">{client["name"]} (ID: {client["id"]})</div>' for client in clients])
    return results


@app.route('/add_order', methods=['POST'])
def add_order():
    client_id = request.form['client_id']
    date = request.form['date']

    # Parse items from form data
    items = []
    form_data = request.form.to_dict(flat=False)

    # Find all keys that match the pattern items[n][field]
    item_keys = [key for key in form_data.keys() if key.startswith('items[')]

    # Group by index
    item_indices = set()
    for key in item_keys:
        # Extract the index from keys like items[0][description]
        index = key.split('[')[1].split(']')[0]
        item_indices.add(index)

    # Build items list
    for index in item_indices:
        item = {
            'description': request.form.get(f'items[{index}][description]'),
            'quantity': request.form.get(f'items[{index}][quantity]'),
            'price_per_unit': request.form.get(f'items[{index}][price_per_unit]')
        }
        items.append(item)

    print(f"Client ID: {client_id}")
    print(f"Date: {date}")
    print(f"Items: {items}")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('INSERT INTO orders (client_id, date) VALUES (?, ?)', (client_id, date))
    order_id = cursor.lastrowid

    for item in items:
        print(f"Adding item: {item}")
        cursor.execute('INSERT INTO order_items (order_id, description, quantity, price_per_unit) VALUES (?, ?, ?, ?)',
                       (order_id, item['description'], item['quantity'], item['price_per_unit']))

    conn.commit()
    conn.close()
    return "Order added successfully! <a href='/'>Back to home</a>"

@app.route('/remove_order', methods=['POST'])
def remove_order():
    order_id = request.form['order_id']

    conn = get_db_connection()
    conn.execute('DELETE FROM orders WHERE id = ?', (order_id,))
    conn.commit()
    conn.close()
    return "Order removed successfully! <a href='/'>Back to home</a>"



@app.route('/order_items/<int:order_id>', methods=['GET'])
def get_order_items(order_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Important: Make sure your cursor returns dictionary-like objects
        cursor.row_factory = sqlite3.Row  # If using SQLite

        cursor.execute('''
            SELECT id, description, quantity, price_per_unit 
            FROM order_items 
            WHERE order_id = ?
        ''', (order_id,))

        items = cursor.fetchall()

        # Convert sqlite3.Row objects to dictionaries
        items_list = []
        for item in items:
            items_list.append({
                'id': item['id'],
                'description': item['description'],
                'quantity': item['quantity'],
                'price_per_unit': item['price_per_unit']
            })

        conn.close()

        # Return JSON response
        return jsonify(items_list)

    except Exception as e:
        print(f"Error fetching order items: {e}")
        return jsonify([]), 500  # Return empty list with error status

@app.route('/generate_invoice/<int:order_id>', methods=['GET'])
def generate_invoice(order_id):
    conn = get_db_connection()
    order = conn.execute('SELECT * FROM orders WHERE id = ?', (order_id,)).fetchone()
    client = conn.execute('SELECT * FROM clients WHERE id = ?', (order['client_id'],)).fetchone()
    items = conn.execute('SELECT * FROM order_items WHERE order_id = ?', (order_id,)).fetchall()
    conn.close()

    if order and client:
        buffer = generate_invoice_pdf(order, client, items)
        return send_file(buffer, as_attachment=False, download_name=f"invoice_{order_id}.pdf", mimetype='application/pdf')
    else:
        return "Order or Client not found", 404

if __name__ == '__main__':
    app.run(debug=True)
