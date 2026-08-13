from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

# Quản lý mức giảm giá từ Admin (Mặc định 15%)
admin_settings = {"discount_percent": 15}

# Danh sách giỏ hàng và danh sách đơn hàng đã đặt
cart = []
orders = []

# --- GIAO DIỆN TRANG KHÁCH HÀNG (GIỮ ĐẦY ĐỦ FORM CŨ + GIỎ HÀNG SHOPEE) ---
CLIENT_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>In 3D - Giỏ Hàng & Khuyến Mãi</title>
    <style>
        * { box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); 
            min-height: 100vh; 
            margin: 0; 
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
            color: #fff;
        }
        .main-container {
            display: flex;
            gap: 20px;
            width: 100%;
            max-width: 950px;
        }
        .card { 
            background: rgba(255, 255, 255, 0.08); 
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 30px; 
            border-radius: 16px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.4); 
            flex: 1;
        }
        h2 { text-align: center; color: #fff; margin-top: 0; margin-bottom: 20px; font-size: 22px; }
        label { font-weight: 500; font-size: 13px; color: #b0bec5; display: block; margin-bottom: 6px; }
        input { 
            width: 100%; padding: 10px 12px; margin-bottom: 12px; 
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2); 
            border-radius: 8px; font-size: 14px; color: #fff;
        }
        input:focus { border-color: #64b5f6; outline: none; background: rgba(255, 255, 255, 0.1); }
        .banner-discount { 
            background: rgba(255, 152, 0, 0.2); border: 1px dashed #ffa726; color: #ffb74d; 
            padding: 10px; text-align: center; font-weight: bold; border-radius: 8px; margin-bottom: 20px; font-size: 14px; 
        }
        .add-btn { 
            width: 100%; padding: 12px; background: linear-gradient(135deg, #3498db, #2980b9); 
            color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; 
        }
        .add-btn:hover { opacity: 0.9; }
        .cart-item { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); padding: 8px 0; font-size: 13px; }
        .price-old { text-decoration: line-through; color: #b0bec5; font-size: 12px; }
        .price-new { color: #ff5252; font-size: 18px; font-weight: bold; }
        .checkout-btn { 
            width: 100%; padding: 12px; background: linear-gradient(135deg, #00b09b, #96c93d); 
            color: white; border: none; border-radius: 8px; font-size: 15px; font-weight: bold; cursor: pointer; margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="main-container">
        <!-- Cột trái: Form nhập yêu cầu cũ đầy đủ -->
        <div class="card">
            <h2>Gửi Yêu Cầu In 3D</h2>
            
            <form action="/add-to-cart" method="POST">
                <label>Họ và tên khách:</label>
                <input type="text" name="customer_name" placeholder="Nhập họ tên của bạn" required>

                <label>Số điện thoại:</label>
                <input type="text" name="phone" placeholder="Nhập số điện thoại" required>

                <label>Địa chỉ nhận hàng:</label>
                <input type="text" name="address" placeholder="Nhập địa chỉ nhận hàng" required>

                <label>Tên mô hình / Vật phẩm cần in:</label>
                <input type="text" name="item_name" placeholder="VD: Mô hình nhân vật..." required>

                <label>Màu sắc nhựa:</label>
                <input type="text" name="color" placeholder="VD: Đỏ, Trắng, Đen..." required>

                <label>Khối lượng ước tính (Gram):</label>
                <input type="number" id="weight" name="weight" placeholder="VD: 50 (2.000đ/g)" step="0.1" required>

                <button type="submit" class="add-btn">➕ Thêm Vào Giỏ Hàng</button>
            </form>
        </div>

        <!-- Cột phải: Giỏ hàng kiểu Shopee + Khuyến mãi từ Admin -->
        <div class="card">
            <h2>🛒 Giỏ Hàng Shopee</h2>

            <div class="banner-discount">
                🔥 Admin đang giảm: <strong>{{ discount }}%</strong>
            </div>

            {% if cart %}
                <div style="max-height: 200px; overflow-y: auto; margin-bottom: 15px;">
                    {% for item in cart %}
                    <div class="cart-item">
                        <div>
                            <strong>{{ item.item_name }}</strong> ({{ item.color }})<br>
                            <small>{{ item.weight }}g — {{"{:,.0f}".format(item.price)}} đ</small>
                        </div>
                        <div>
                            <a href="/remove/{{ item.id }}" style="color: #ff5252; text-decoration: none; font-weight: bold;">Xóa</a>
                        </div>
                    </div>
                    {% endfor %}
                </div>

                <div style="border-top: 1px dashed rgba(255,255,255,0.3); padding-top: 10px;">
                    <p style="margin: 5px 0;">Tổng tiền gốc: <span class="price-old">{{"{:,.0f}".format(total_original)}} đ</span></p>
                    <p style="margin: 5px 0;">Được giảm ({{ discount }}%): <span style="color: #69f0ae;">-{{"{:,.0f}".format(total_original * discount / 100)}} đ</span></p>
                    <p style="margin: 5px 0;">Thành tiền thanh toán:</p>
                    <div class="price-new">{{"{:,.0f}".format(total_final)}} đ</div>
                    
                    <form action="/checkout" method="POST">
                        <button type="submit" class="checkout-btn">ĐẶT HÀNG NGAY</button>
                    </form>
                </div>
            {% else %}
                <p style="color: #b0bec5; text-align: center; margin-top: 40px;">Giỏ hàng của bạn đang trống.</p>
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
        .box { background: white; padding: 25px; border-radius: 8px; max-width: 1100px; margin: 0 auto 20px auto; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h2 { color: #333; margin-top: 0; }
        input { padding: 8px; width: 200px; border: 1px solid #ccc; border-radius: 4px; }
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
        <h2>📋 Quản Lý Danh Sách Đơn Đặt Hàng</h2>
        <table>
            <tr>
                <th>Khách hàng</th>
                <th>SĐT</th>
                <th>Địa chỉ</th>
                <th>Sản phẩm đặt in</th>
                <th>Thành tiền (Đã giảm)</th>
            </tr>
            {% for o in orders %}
            <tr>
                <td>{{ o.name }}</td>
                <td>{{ o.phone }}</td>
                <td>{{ o.address }}</td>
                <td>{{ o.details }}</td>
                <td style="color: #e74c3c; font-weight: bold;">{{"{:,.0f}".format(o.total)}} đ</td>
            </tr>
            {% else %}
            <tr><td colspan="5" style="text-align: center; color: #888; padding: 20px;">Chưa có đơn hàng nào.</td></tr>
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
  global customer_info
  # Lưu tạm thông tin khách hàng vào session/biến toàn cục để dùng khi checkout
  app.config["TEMP_CUSTOMER"] = {
      "name": request.form.get("customer_name"),
      "phone": request.form.get("phone"),
      "address": request.form.get("address"),
  }

  item_name = request.form.get("item_name")
  color = request.form.get("color")
  weight = float(request.form.get("weight", 0))
  price = weight * 2000  # 2.000đ / gram

  new_item = {
      "id": len(cart) + 1,
      "item_name": item_name,
      "color": color,
      "weight": weight,
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
  info = app.config.get(
      "TEMP_CUSTOMER", {"name": "Khách lẻ", "phone": "Không có", "address": "Không có"}
  )

  total_original = sum(item["price"] for item in cart)
  discount = admin_settings["discount_percent"]
  total_final = total_original - (total_original * discount / 100)

  details = ", ".join([f"{i['item_name']} ({i['weight']}g)" for i in cart])

  if cart:
    orders.append({
        "name": info["name"],
        "phone": info["phone"],
        "address": info["address"],
        "details": details,
        "total": total_final,
    })
    cart.clear()

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
