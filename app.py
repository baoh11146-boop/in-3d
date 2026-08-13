from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

# Quản lý mức giảm giá từ Admin (Mặc định 15%)
admin_settings = {"discount_percent": 15}

# Danh sách giỏ hàng và đơn hàng
cart = []
orders = []

# --- GIAO DIỆN TRANG KHÁCH HÀNG ---
CLIENT_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Đặt Hàng In 3D - Giỏ Hàng Shopee</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; color: #333; }
        .header { background: linear-gradient(135deg, #ee4d2d, #ff7337); color: white; padding: 20px; border-radius: 8px; text-align: center; margin-bottom: 20px; }
        .banner-discount { background: #fff8e1; border: 1px dashed #ffa000; color: #ff8f00; padding: 12px; text-align: center; font-weight: bold; border-radius: 6px; margin-bottom: 20px; font-size: 16px; }
        .container { display: flex; gap: 20px; max-width: 1200px; margin: 0 auto; }
        .form-box { flex: 2; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
        .cart-box { flex: 1; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); height: fit-content; }
        label { font-weight: 600; font-size: 13px; color: #555; display: block; margin-bottom: 6px; }
        input, select { width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 6px; box-sizing: border-box; }
        button { background: #ee4d2d; color: white; border: none; padding: 12px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; font-size: 15px; }
        button:hover { background: #d73211; }
        .cart-item { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding: 10px 0; font-size: 14px; }
        .total-section { margin-top: 15px; border-top: 2px solid #eee; padding-top: 10px; }
        .price-old { text-decoration: line-through; color: #888; font-size: 13px; }
        .price-new { color: #ee4d2d; font-weight: bold; font-size: 20px; text-align: right; margin-top: 5px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🖨️ Dịch Vụ In 3D Theo Yêu Cầu</h1>
        <p>Thêm sản phẩm vào giỏ hàng và áp dụng giảm giá tự động</p>
    </div>

    <!-- Thông báo mức giảm giá lấy trực tiếp từ Admin -->
    <div class="banner-discount">
        🔥 ĐANG KHUYẾN MÃI: Giảm ngay <strong>{{ discount }}%</strong> trên tổng đơn hàng hôm nay!
    </div>

    <div class="container">
        <!-- Form điền thông tin sản phẩm in 3D -->
        <div class="form-box">
            <h2>📝 Nhập Yêu Cầu In 3D</h2>
            <form action="/add-to-cart" method="POST">
                <label>Tên mô hình / Vật phẩm:</label>
                <input type="text" name="item_name" placeholder="VD: Bánh răng, Mô hình xe..." required>

                <label>Màu sắc nhựa:</label>
                <input type="text" name="color" placeholder="VD: Đỏ, Trắng, Đen, Xanh..." required>

                <label>Khối lượng ước tính (Gram):</label>
                <input type="number" name="weight" placeholder="VD: 50 (Giá: 2.000đ/g)" step="0.1" required>

                <label>Số lượng:</label>
                <input type="number" name="quantity" value="1" min="1" required>

                <button type="submit">🛒 Thêm Vào Giỏ Hàng</button>
            </form>
        </div>

        <!-- Giỏ hàng kiểu Shopee -->
        <div class="cart-box">
            <h2>🛍️ Giỏ Hàng Của Bạn</h2>
            {% if cart %}
                {% for item in cart %}
                <div class="cart-item">
                    <div>
                        <strong>{{ item.item_name }}</strong> ({{ item.color }})<br>
                        <small>{{ item.weight }}g x {{ item.quantity }} cái = {{"{:,.0f}".format(item.price)}} đ</small>
                    </div>
                    <div>
                        <a href="/remove/{{ item.id }}" style="color: #e74c3c; text-decoration: none; font-weight: bold;">Xóa</a>
                    </div>
                </div>
                {% endfor %}

                <div class="total-section">
                    <p>Tổng tiền gốc: <span class="price-old">{{"{:,.0f}".format(total_original)}} đ</span></p>
                    <p>Được giảm giá ({{ discount }}%): <span style="color: #27ae60; font-weight: bold;">-{{"{:,.0f}".format(total_original * discount / 100)}} đ</span></p>
                    <p>Thành tiền thanh toán:</p>
                    <div class="price-new">{{"{:,.0f}".format(total_final)}} đ</div>
                    
                    <form action="/checkout" method="POST" style="margin-top: 15px;">
                        <label>Họ tên người nhận:</label>
                        <input type="text" name="customer_name" placeholder="Nhập họ tên" required style="margin-bottom: 8px;">
                        
                        <label>Số điện thoại:</label>
                        <input type="text" name="phone" placeholder="Nhập SĐT" required style="margin-bottom: 12px;">
                        
                        <button type="submit" style="background: #26aa99;">ĐẶT HÀNG NGAY</button>
                    </form>
                </div>
            {% else %}
                <p style="color: #888; text-align: center; margin-top: 30px;">Giỏ hàng của bạn đang trống.</p>
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
        .box { background: white; padding: 25px; border-radius: 8px; max-width: 1000px; margin: 0 auto 20px auto; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h2 { color: #333; margin-top: 0; }
        input { padding: 8px; width: 220px; border: 1px solid #ccc; border-radius: 4px; }
        button { padding: 8px 16px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #ddd; padding: 10px; text-align: left; font-size: 14px; }
        th { background: #007bff; color: white; }
    </style>
</head>
<body>
    <div class="box">
        <h2>⚙️ Quản Lý Mức Giảm Giá Toàn Trang</h2>
        <form action="/admin/update-discount" method="POST">
            <label>Nhập phần trăm giảm giá (%) áp dụng cho khách:</label><br><br>
            <input type="number" name="discount_percent" value="{{ discount }}" min="0" max="100" required>
            <button type="submit">Cập Nhật Mức Giảm</button>
        </form>
    </div>

    <div class="box">
        <h2>📋 Quản Lý Đơn Hàng Đã Đặt</h2>
        <table>
            <tr>
                <th>Khách hàng</th>
                <th>SĐT</th>
                <th>Sản phẩm đặt in</th>
                <th>Thành tiền (Đã giảm)</th>
            </tr>
            {% for o in orders %}
            <tr>
                <td>{{ o.name }}</td>
                <td>{{ o.phone }}</td>
                <td>{{ o.details }}</td>
                <td style="color: #e74c3c; font-weight: bold;">{{"{:,.0f}".format(o.total)}} đ</td>
            </tr>
            {% else %}
            <tr><td colspan="4" style="text-align: center; color: #888; padding: 20px;">Chưa có đơn hàng nào.</td></tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
"""


@app.route("/")
def index():
  total_original = sum(item["price"] for item in cart)
  discount = admin_settings["discount_percent"]
  total_final = total_original - (total_original * discount / 100)

  return render_template_string(
      CLIENT_HTML,
      cart=cart,
      discount=discount,
      total_original=total_original,
      total_final=total_final,
  )


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
  item_name = request.form.get("item_name")
  color = request.form.get("color")
  weight = float(request.form.get("weight", 0))
  quantity = int(request.form.get("quantity", 1))

  # Tính giá: 2.000đ mỗi gram * số lượng
  price = weight * 2000 * quantity

  new_item = {
      "id": len(cart) + 1,
      "item_name": item_name,
      "color": color,
      "weight": weight,
      "quantity": quantity,
      "price": price,
  }
  cart.append(new_item)
  return redirect(url_for("index"))


@app.route("/remove/<int:item_id>")
def remove_from_cart(item_id):
  global cart
  cart = [item for item in cart if item["id"] != item_id]
  return redirect(url_for("index"))


@app.route("/checkout", methods=["POST"])
def checkout():
  name = request.form.get("customer_name")
  phone = request.form.get("phone")

  total_original = sum(item["price"] for item in cart)
  discount = admin_settings["discount_percent"]
  total_final = total_original - (total_original * discount / 100)

  # Gom tên các sản phẩm lại thành một chuỗi ghi chú đơn hàng
  details = ", ".join(
      [f"{i['item_name']} ({i['quantity']} cái)" for i in cart]
  )

  if cart:
    orders.append({"name": name, "phone": phone, "details": details, "total": total_final})
    cart.clear()  # Đặt hàng thành công thì xóa sạch giỏ hàng

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
