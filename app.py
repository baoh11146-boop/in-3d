from flask import Flask, redirect, render_template_string, request, session, url_for

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Cấu hình mức giảm giá toàn trang
admin_settings = {"discount_percent": 15}

# Dữ liệu giỏ hàng và danh sách đơn hàng
cart = []
orders = []

# --- GIAO DIỆN TRANG KHÁCH HÀNG ---
CLIENT_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>In 3D - Giỏ Hàng Shopee</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f5f5f5; margin: 0; padding: 20px; color: #333; }
        .container { display: flex; gap: 20px; max-width: 1000px; margin: auto; }
        .box { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); flex: 1; }
        label { font-weight: bold; font-size: 13px; color: #555; display: block; margin-bottom: 5px; }
        input { width: 100%; padding: 10px; margin-bottom: 12px; border: 1px solid #ddd; border-radius: 4px; box-sizing: border-box; }
        button { width: 100%; padding: 12px; background: #ee4d2d; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #d73211; }
        .banner { background: #fff8e1; border: 1px dashed #ffa000; color: #ff8f00; padding: 10px; text-align: center; font-weight: bold; border-radius: 4px; margin-bottom: 15px; }
        .cart-item { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #eee; padding: 8px 0; font-size: 14px; }
    </style>
</head>
<body>
    <div class="container">
        <!-- Cột trái: Thông tin và sản phẩm -->
        <form action="/add-to-cart" method="POST" class="box">
            <h2>📝 Thông Tin & Sản Phẩm</h2>
            
            <label>Họ và tên:</label>
            <input type="text" name="customer_name" value="{{ info.name }}" placeholder="Nhập họ tên" required>
            
            <label>Số điện thoại:</label>
            <input type="text" name="phone" value="{{ info.phone }}" placeholder="Nhập SĐT" required>
            
            <label>Địa chỉ nhận hàng:</label>
            <input type="text" name="address" value="{{ info.address }}" placeholder="Nhập địa chỉ" required>
            
            <hr style="border: 0; border-top: 1px solid #eee; margin: 15px 0;">
            
            <label>Tên mô hình in 3D:</label>
            <input type="text" name="item_name" placeholder="VD: Bánh răng, Mô hình..." required>
            
            <label>Màu sắc nhựa:</label>
            <input type="text" name="color" placeholder="VD: Đỏ, Trắng, Đen..." required>
            
            <label>Khối lượng (Gram):</label>
            <input type="number" name="weight" placeholder="VD: 50 (2.000đ/g)" step="0.1" required>
            
            <button type="submit">🛒 Thêm Vào Giỏ Hàng</button>
        </form>

        <!-- Cột phải: Giỏ hàng -->
        <div class="box">
            <div class="banner">🔥 Đang giảm giá: {{ discount }}%</div>
            <h2>🛒 Giỏ Hàng Của Bạn</h2>
            
            {% if cart %}
                {% for item in cart %}
                <div class="cart-item">
                    <div>
                        <strong>{{ item.item_name }}</strong> ({{ item.color }}, {{ item.weight }}g)<br>
                        <span style="color: #ee4d2d; font-weight: bold;">{{"{:,.0f}".format(item.price)}} đ</span>
                    </div>
                    <div>
                        <a href="/remove/{{ item.id }}" style="color: red; text-decoration: none; font-weight: bold;">Xóa</a>
                    </div>
                </div>
                {% endfor %}
                
                <div style="margin-top: 20px; border-top: 2px solid #eee; padding-top: 10px;">
                    <p>Tổng gốc: <span style="text-decoration: line-through; color: #888;">{{"{:,.0f}".format(total_original)}} đ</span></p>
                    <p>Giảm giá ({{ discount }}%): <span style="color: green;">-{{"{:,.0f}".format(total_original * discount / 100)}} đ</span></p>
                    <h3>Thành tiền: <span style="color: #ee4d2d;">{{"{:,.0f}".format(total_final)}} đ</span></h3>
                    
                    <form action="/checkout" method="POST" style="margin-top: 15px;">
                        <button type="submit" style="background: #26aa99;">ĐẶT HÀNG NGAY</button>
                    </form>
                </div>
            {% else %}
                <p style="color: #888; text-align: center; margin-top: 40px;">Giỏ hàng trống.</p>
            {% endif %}
        </div>
    </div>
</body>
</html>
"""

# --- GIAO DIỆN TRANG ADMIN (ĐÃ NÂNG CẤP GIAO DIỆN XỊN SÒ) ---
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Trang Quản Trị Admin - In 3D</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }
        .admin-container { max-width: 1000px; margin: auto; display: flex; flex-direction: column; gap: 20px; }
        .box { background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        h2 { color: #2c3e50; margin-top: 0; border-bottom: 2px solid #eee; padding-bottom: 10px; }
        label { font-weight: bold; font-size: 14px; color: #555; }
        input { padding: 10px; width: 250px; border: 1px solid #ccc; border-radius: 4px; margin-right: 10px; }
        button { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold; }
        button:hover { background: #0056b3; }
        table { width: 100%; border-collapse: collapse; margin-top: 15px; }
        th, td { border: 1px solid #e1e1e1; padding: 12px; text-align: left; font-size: 14px; }
        th { background: #f8f9fa; color: #333; font-weight: bold; }
        tr:nth-child(even) { background: #fafafa; }
        .badge { background: #e3f2fd; color: #1976d2; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px; }
    </style>
</head>
<body>
    <div class="admin-container">
        <!-- Hộp chỉnh sửa giảm giá -->
        <div class="box">
            <h2>⚙️ Cấu Hình Chương Trình Khuyến Mãi</h2>
            <form action="/admin/update-discount" method="POST" style="display: flex; align-items: center; gap: 10px; margin-top: 15px;">
                <label>Phần trăm giảm giá (%):</label>
                <input type="number" name="discount_percent" value="{{ discount }}" min="0" max="100" required>
                <button type="submit">💾 Cập Nhật Ngay</button>
            </form>
        </div>

        <!-- Hộp danh sách đơn hàng -->
        <div class="box">
            <h2>📋 Quản Lý Đơn Hàng Khách Đã Đặt</h2>
            <table>
                <tr>
                    <th>Khách hàng</th>
                    <th>Số điện thoại</th>
                    <th>Địa chỉ giao</th>
                    <th>Sản phẩm đặt in</th>
                    <th>Thành tiền (Đã giảm)</th>
                </tr>
                {% for o in orders %}
                <tr>
                    <td><strong>{{ o.name }}</strong></td>
                    <td>{{ o.phone }}</td>
                    <td>{{ o.address }}</td>
                    <td><span class="badge">{{ o.details }}</span></td>
                    <td style="color: #e74c3c; font-weight: bold; font-size: 15px;">{{"{:,.0f}".format(o.total)}} đ</td>
                </tr>
                {% else %}
                <tr>
                    <td colspan="5" style="text-align: center; color: #888; padding: 30px;">Chưa có đơn hàng nào được đặt.</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  info = session.get("customer_info", {"name": "", "phone": "", "address": ""})

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

  return render_template_string(
      CLIENT_HTML,
      cart=cart,
      info=info,
      discount=discount,
      total_original=total_original,
      total_final=total_final,
  )


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
  session["customer_info"] = {
      "name": request.form.get("customer_name"),
      "phone": request.form.get("phone"),
      "address": request.form.get("address"),
  }

  weight = float(request.form.get("weight", 0))
  item = {
      "id": len(cart) + 1,
      "item_name": request.form.get("item_name"),
      "color": request.form.get("color"),
      "weight": weight,
      "price": weight * 2000,
  }
  cart.append(item)
  return redirect(url_for("index"))


@app.route("/remove/<int:id>")
def remove(id):
  global cart
  cart = [i for i in cart if i["id"] != id]
  return redirect(url_for("index"))


@app.route("/checkout", methods=["POST"])
def checkout():
  info = session.get(
      "customer_info", {"name": "Khách", "phone": "Trống", "address": "Trống"}
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
