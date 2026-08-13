from flask import Flask, redirect, render_template_string, request, url_for, session

app = Flask(__name__)
app.secret_key = 'supersecretkey' # Cần key này để lưu thông tin khách hàng tạm thời

# Cấu hình mức giảm giá
admin_settings = {"discount_percent": 15}

# Dữ liệu
cart = []
orders = []

CLIENT_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>In 3D - Giỏ Hàng Shopee</title>
    <style>
        body { font-family: sans-serif; background: #f5f5f5; padding: 20px; }
        .container { display: flex; gap: 20px; max-width: 1000px; margin: auto; }
        .box { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; }
        input { width: 100%; padding: 10px; margin: 5px 0 15px 0; border: 1px solid #ccc; border-radius: 4px; }
        button { width: 100%; padding: 10px; background: #ee4d2d; color: white; border: none; border-radius: 4px; cursor: pointer; }
    </style>
</head>
<body>
    <div class="container">
        <form action="/add-to-cart" method="POST" class="box">
            <h2>Thông tin đặt hàng</h2>
            <label>Họ tên:</label>
            <input type="text" name="customer_name" value="{{ info.name }}" required>
            <label>SĐT:</label>
            <input type="text" name="phone" value="{{ info.phone }}" required>
            <label>Địa chỉ:</label>
            <input type="text" name="address" value="{{ info.address }}" required>
            
            <hr>
            <h2>Sản phẩm in 3D</h2>
            <label>Tên mô hình:</label>
            <input type="text" name="item_name" required>
            <label>Màu sắc:</label>
            <input type="text" name="color" required>
            <label>Khối lượng (g):</label>
            <input type="number" name="weight" step="0.1" required>
            <button type="submit">🛒 Thêm vào giỏ hàng</button>
        </form>

        <div class="box">
            <h2>Giỏ hàng (Giảm {{ discount }}%)</h2>
            {% for item in cart %}
            <p>{{ item.item_name }} ({{ item.weight }}g) - {{"{:,.0f}".format(item.price)}}đ 
               <a href="/remove/{{ item.id }}">Xóa</a></p>
            {% endfor %}
            <hr>
            <p>Tổng tiền: {{"{:,.0f}".format(total_final)}} đ</p>
            <form action="/checkout" method="POST">
                <button style="background: #26aa99;">ĐẶT HÀNG NGAY</button>
            </form>
        </div>
    </div>
</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    # Lấy thông tin đã nhập từ session nếu có
    info = session.get("customer_info", {"name": "", "phone": "", "address": ""})
    
    # Cập nhật thông tin khách hàng nếu có gửi từ form
    if request.method == "POST":
        info = {
            "name": request.form.get("customer_name"),
            "phone": request.form.get("phone"),
            "address": request.form.get("address"),
        }
        session["customer_info"] = info

    total_original = sum(item["price"] for item in cart)
    discount = admin_settings["discount_percent"]
    total_final = total_original - (total_original * discount / 100)
    
    return render_template_string(CLIENT_HTML, cart=cart, info=info, discount=discount, total_final=total_final)

@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    # Lưu thông tin khách vào session ngay khi thêm món
    session["customer_info"] = {
        "name": request.form.get("customer_name"),
        "phone": request.form.get("phone"),
        "address": request.form.get("address"),
    }
    
    item = {
        "id": len(cart),
        "item_name": request.form.get("item_name"),
        "color": request.form.get("color"),
        "weight": float(request.form.get("weight")),
        "price": float(request.form.get("weight")) * 2000
    }
    cart.append(item)
    return redirect("/")

@app.route("/remove/<int:id>")
def remove(id):
    global cart
    cart = [i for i in cart if i["id"] != id]
    return redirect("/")

@app.route("/checkout", methods=["POST"])
def checkout():
    info = session.get("customer_info")
    total_original = sum(item["price"] for item in cart)
    total_final = total_original - (total_original * admin_settings["discount_percent"] / 100)
    
    orders.append({"info": info, "total": total_final, "items": [i['item_name'] for i in cart]})
    cart.clear()
    return "Đặt hàng thành công! <a href='/'>Quay lại</a>"

@app.route("/admin")
def admin():
    return render_template_string("<h2>Đơn hàng</h2>{% for o in orders %}<p>{{o}}</p>{% endfor %}", orders=orders)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
