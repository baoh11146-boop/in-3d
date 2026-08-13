from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

# Dữ liệu mẫu trang Admin quản lý:
# 1. % Giảm giá toàn hệ thống (Admin thay đổi ở đây, khách hàng sẽ thấy bên ngoài)
admin_settings = {"discount_percent": 15}  # Mặc định giảm 15%

# 2. Danh sách sản phẩm in 3D mẫu
products = [
    {"id": 1, "name": "Mô hình Siêu xe 3D", "price": 150000, "image": "🏎️"},
    {"id": 2, "name": "Bánh răng cơ khí", "price": 50000, "image": "⚙️"},
    {"id": 3, "name": "Mô hình Nhân vật Anime", "price": 200000, "image": "🤖"},
]

# Giỏ hàng lưu tạm (Mỗi khách là một danh sách item trong giỏ)
cart = []

# Đơn hàng đã đặt
orders = []

# --- GIAO DIỆN TRANG KHÁCH HÀNG ---
CLIENT_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Cửa Hàng In 3D - Giỏ Hàng Shopee Style</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; color: #333; }
        .header { background: linear-gradient(135deg, #ee4d2d, #ff7337); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
        .banner-discount { background: #fff8e1; border: 1px dashed #ffa000; color: #ff8f00; padding: 10px; text-align: center; font-weight: bold; border-radius: 6px; margin-bottom: 20px; }
        .container { display: flex; gap: 20px; max-width: 1200px; margin: 0 auto; }
        .product-list { flex: 2; display: grid; grid-template-columns: repeat(auto-fill, minmax(220px, 1fr)); gap: 15px; }
        .product-card { background: white; padding: 15px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }
        .product-icon { font-size: 40px; margin-bottom: 10px; }
        .cart-box { flex: 1; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: fit-content; }
        button { background: #ee4d2d; color: white; border: none; padding: 8px 15px; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #d73211; }
        .cart-item { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding: 10px 0; font-size: 14px; }
        .total-section { margin-top: 15px; font-size: 16px; border-top: 2px solid #eee; padding-top: 10px; }
        .price-old { text-decoration: line-through; color: #888; font-size: 13px; }
        .price-new { color: #ee4d2d; font-weight: bold; font-size: 18px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🛍️ Thế Giới In 3D Theo Yêu Cầu</h1>
        <p>Mua sắm thông minh - Giao hàng nhanh chóng</p>
    </div>

    <!-- Thông báo mức giảm giá từ Admin -->
    <div class="banner-discount">
        🔥 CHƯƠNG TRÌNH KHUYẾN MÃI HOT: Đang giảm giá trực tiếp <strong>{{ discount }}%</strong> cho toàn bộ giỏ hàng và sản phẩm hôm nay!
    </div>

    <div class="container">
        <!-- Danh sách sản phẩm -->
        <div class="product-list">
            {% for p in products %}
            <div class="product-card">
                <div class="product-icon">{{ p.image }}</div>
                <h3>{{ p.name }}</h3>
                <p style="color: #ee4d2d; font-weight: bold;">{{"{:,.0f}".format(p.price)}} đ</p>
                <form action="/add-to-cart/{{ p.id }}" method="POST">
                    <button type="submit">➕ Thêm vào giỏ hàng</button>
                </form>
            </div>
            {% endfor %}
        </div>

        <!-- Giỏ hàng kiểu Shopee -->
        <div class="cart-box">
            <h2>🛒 Giỏ Hàng Của Bạn</h2>
            {% if cart %}
                {% for item in cart %}
                <div class="cart-item">
                    <div>
                        <strong>{{ item.name }}</strong><br>
                        <small>{{"{:,.0f}".format(item.price)}} đ x {{ item.qty }}</small>
                    </div>
                    <div>
                        <a href="/remove/{{ item.id }}" style="color: red; text-decoration: none; font-weight: bold;">Xóa</a>
                    </div>
                </div>
                {% endfor %}

                <div class="total-section">
                    <p>Tổng tiền gốc: <span class="price-old">{{"{:,.0f}".format(total_original)}} đ</span></p>
                    <p>Được giảm giá ({{ discount }}%): <span style="color: green;">-{{"{:,.0f}".format(total_original * discount / 100)}} đ</span></p>
                    <p>Thành tiền thanh toán:</p>
                    <div class="price-new">{{"{:,.0f}".format(total_final)}} đ</div>
                    
                    <form action="/checkout" method="POST" style="margin-top: 15px;">
                        <input type="text" name="customer_name" placeholder="Họ tên người nhận" required style="width: 100%; padding: 8px; margin-bottom: 8px; box-sizing: border-box;">
                        <input type="text" name="phone" placeholder="Số điện thoại" required style="width: 100%; padding: 8px; margin-bottom: 12px; box-sizing: border-box;">
                        <button type="submit" style="width: 100%; padding: 12px; background: #26aa99;">ĐẶT HÀNG NGAY</button>
                    </form>
                </div>
            {% else %}
                <p style="color: #888; text-align: center;">Giỏ hàng đang trống.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- GIAO DIỆN TRANG ADMIN ---
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Trang Quản Trị Admin</title>
    <style>
        body { font-family: Arial, sans-serif; background: #f0f2f5; padding: 30px; }
        .box { background: white; padding: 25px; border-radius: 8px; max-width: 800px; margin: 0 auto 20px auto; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h2 { color: #333; margin-top: 0; }
        input { padding: 8px; width: 200px; }
        button { padding: 8px 15px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }
        th { background: #007bff; color: white; }
    </style>
</head>
<body>
    <div class="box">
        <h2>⚙️ Cài Đặt Giảm Giá Toàn Trang</h2>
        <form action="/admin/update-discount" method="POST">
            <label>Phần trăm giảm giá (%) cho khách hàng:</label><br><br>
            <input type="number" name="discount_percent" value="{{ discount }}" min="0" max="100" required>
            <button type="submit">Cập Nhật Mức Giảm</button>
        </form>
    </div>

    <div class="box">
        <h2>📦 Quản Lý Đơn Hàng Đã Đặt</h2>
        <table>
            <tr>
                <th>Khách hàng</th>
                <th>SĐT</th>
                <th>Tổng thanh toán</th>
            </tr>
            {% for o in orders %}
            <tr>
                <td>{{ o.name }}</td>
                <td>{{ o.phone }}</td>
                <td style="color: red; font-weight: bold;">{{"{:,.0f}".format(o.total)}} đ</td>
            </tr>
            {% else %}
            <tr><td colspan="3" style="text-align: center; color: #888;">Chưa có đơn hàng nào.</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
  # Tính tổng tiền giỏ hàng
  total_original = sum(item["price"] * item["qty"] for item in cart)
  discount = admin_settings["discount_percent"]
  total_final = total_original - (total_original * discount / 100)

  return render_template_string(
      CLIENT_HTML,
      products=products,
      cart=cart,
      discount=discount,
      total_original=total_original,
      total_final=total_final,
  )


@app.route("/add-to-cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
  # Tìm sản phẩm
  product = next((p for p in products if p["id"] == product_id), None)
  if product:
    # Kiểm tra xem sản phẩm đã có trong giỏ hàng chưa
    existing = next((item for item in cart if item["id"] == product_id), None)
    if existing:
      existing["qty"] += 1
    else:
      cart.append({
          "id": product["id"],
          "name": product["name"],
          "price": product["price"],
          "qty": 1,
      })
  return redirect(url_for("index"))


@app.route("/remove/<int:product_id>")
def remove_from_cart(product_id):
  global cart
  cart = [item for item in cart if item["id"] != product_id]
  return redirect(url_for("index"))


@app.route("/checkout", methods=["POST"])
def checkout():
  name = request.form.get("customer_name")
  phone = request.form.get("phone")
  total_original = sum(item["price"] * item["qty"] for item in cart)
  discount = admin_settings["discount_percent"]
  total_final = total_original - (total_original * discount / 100)

  if cart:
    orders.append({"name": name, "phone": phone, "total": total_final})
    cart.clear()  # Thanh toán xong thì xóa giỏ hàng
  return redirect(url_for("index"))


@app.route("/admin")
def admin():
  return render_template_string(
      ADMIN_HTML, discount=admin_settings["discount_percent"], orders=orders
  )


@app.route("/admin/update-discount", methods=["POST"])
def update_discount():
  new_discount = int(request.form.get("discount_percent", 0))
  admin_settings["discount_percent"] = new_discount
  return redirect(url_for("admin"))


if __name__ == "__main__":
  app.run(host="0.0.0.0", port=10000)
