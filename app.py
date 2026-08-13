from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

# Danh sách lưu trữ đơn hàng
orders = []

# Giao diện trang Khách hàng (Đã dọn sạch thanh menu, không còn chữ Home/Admin)
INDEX_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Dịch Vụ In 3D Theo Yêu Cầu</title>
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
        .card { 
            background: rgba(255, 255, 255, 0.08); 
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.15);
            padding: 40px; 
            border-radius: 16px; 
            box-shadow: 0 15px 35px rgba(0,0,0,0.4); 
            width: 100%; 
            max-width: 500px; 
        }
        h2 { 
            text-align: center; 
            color: #fff; 
            margin-top: 0;
            margin-bottom: 25px; 
            font-size: 26px;
            font-weight: 600;
        }
        label { 
            font-weight: 500; 
            font-size: 13px; 
            color: #b0bec5; 
            display: block; 
            margin-bottom: 6px; 
        }
        input { 
            width: 100%; 
            padding: 12px 15px; 
            margin-bottom: 18px; 
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.2); 
            border-radius: 8px; 
            font-size: 14px; 
            color: #fff;
            transition: all 0.3s;
        }
        input::placeholder { color: #78909c; }
        input:focus { 
            border-color: #64b5f6; 
            outline: none; 
            box-shadow: 0 0 10px rgba(100, 181, 246, 0.3); 
            background: rgba(255, 255, 255, 0.1);
        }
        .price-box { 
            background: rgba(0, 0, 0, 0.2); 
            border: 2px dashed rgba(255, 255, 255, 0.3); 
            padding: 15px; 
            border-radius: 8px; 
            text-align: center; 
            font-size: 22px; 
            font-weight: bold; 
            color: #ff5252; 
            margin-bottom: 20px; 
        }
        button { 
            width: 100%; 
            padding: 14px; 
            background: linear-gradient(135deg, #00b09b, #96c93d); 
            color: white; 
            border: none; 
            border-radius: 8px; 
            font-size: 16px; 
            font-weight: bold; 
            cursor: pointer; 
            transition: opacity 0.3s, transform 0.2s;
        }
        button:hover { opacity: 0.9; transform: translateY(-2px); }
        .alert { 
            background: rgba(46, 204, 113, 0.2); 
            color: #2ecc71; 
            border: 1px solid #2ecc71;
            padding: 14px; 
            border-radius: 8px; 
            text-align: center; 
            margin-bottom: 20px; 
            font-weight: 600; 
        }
    </style>
    <script>
        function calculatePrice() {
            let weight = document.getElementById('weight').value;
            let total = weight ? weight * 2000 : 0;
            document.getElementById('estimated-price').innerText = total.toLocaleString('vi-VN') + ' đ';
        }
    </script>
</head>
<body>
    <div class="card">
        <h2>Gửi Yêu Cầu In 3D</h2>
        {% if success %}
        <div class="alert">🎉 Đặt hàng thành công! Chúng tôi sẽ liên hệ lại sớm nhất.</div>
        {% endif %}
        <form method="POST">
            <label>Họ và tên khách:</label>
            <input type="text" name="customer_name" placeholder="Nhập họ tên của bạn" required>
            <label>Số điện thoại:</label>
            <input type="text" name="phone" placeholder="Nhập số điện thoại liên hệ" required>
            <label>Địa chỉ nhận hàng:</label>
            <input type="text" name="address" placeholder="Nhập số nhà, tên đường, khu vực..." required>
            <label>Tên mô hình / Vật phẩm cần in:</label>
            <input type="text" name="item_name" placeholder="VD: Mô hình nhân vật, bánh răng..." required>
            <label>Màu sắc nhựa:</label>
            <input type="text" name="color" placeholder="VD: Đỏ, Trắng, Đen, Xanh..." required>
            <label>Khối lượng ước tính (Gram):</label>
            <input type="number" id="weight" name="weight" placeholder="VD: 50" step="0.1" oninput="calculatePrice()" required>
            <label>Tạm tính giá tiền:</label>
            <div class="price-box" id="estimated-price">0 đ</div>
            <button type="submit">Gửi Yêu Cầu Đặt Hàng</button>
        </form>
    </div>
</body>
</html>
"""

# Giao diện trang Admin (Quản lý đơn hàng)
ADMIN_HTML = """
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <title>Trang Quản Lý Đơn Hàng (Admin)</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, sans-serif; padding: 40px; background: #f4f6f9; margin: 0; }
        .container { max-width: 1250px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        h2 { color: #2c3e50; margin-top: 0; margin-bottom: 20px; border-bottom: 2px solid #ecf0f1; padding-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { padding: 12px 14px; text-align: left; border-bottom: 1px solid #e9ecef; font-size: 14px; }
        th { background: #2c3e50; color: white; font-weight: 600; }
        tr:hover { background: #f8f9fa; }
        .action-btns { display: flex; gap: 6px; }
        .complete-btn { background: #27ae60; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-weight: 600; }
        .complete-btn:hover { background: #219653; }
        .delete-btn { background: #e74c3c; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-weight: 600; }
        .delete-btn:hover { background: #c0392b; }
        .empty-row { text-align: center; color: #95a5a6; padding: 30px; font-style: italic; }
        .badge { background: #e1f5fe; color: #0288d1; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
        .status-doing { background: #fff3cd; color: #856404; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
        .status-done { background: #d4edda; color: #155724; padding: 4px 8px; border-radius: 4px; font-weight: 600; }
    </style>
</head>
<body>
<div class="container">
    <h2>📋 Quản Lý Danh Sách Đơn Đặt Hàng In 3D</h2>
    <table>
        <thead>
            <tr>
                <th>ID</th>
                <th>Khách hàng</th>
                <th>Số điện thoại</th>
                <th>Địa chỉ nhà</th>
                <th>Sản phẩm</th>
                <th>Màu sắc</th>
                <th>Khối lượng</th>
                <th>Thành tiền</th>
                <th>Trạng thái</th>
                <th>Hành động</th>
            </tr>
        </thead>
        <tbody>
            {% for order in orders %}
            <tr>
                <td><strong>#{{ order.id }}</strong></td>
                <td>{{ order.customer_name }}</td>
                <td>{{ order.phone }}</td>
                <td>{{ order.address }}</td>
                <td>{{ order.item_name }}</td>
                <td><span class="badge">{{ order.color }}</span></td>
                <td>{{ order.weight }}g</td>
                <td><strong style="color: #e74c3c;">{{"{:,.0f}".format(order.total_price)}} đ</strong></td>
                <td>
                    {% if order.status == 'Đã giao' %}
                        <span class="status-done">Đã giao</span>
                    {% else %}
                        <span class="status-doing">Chưa làm</span>
                    {% endif %}
                </td>
                <td>
                    <div class="action-btns">
                        {% if order.status != 'Đã giao' %}
                        <form action="{{ url_for('complete_order', order_id=order.id) }}" method="POST" style="margin:0;">
                            <button type="submit" class="complete-btn">Xong</button>
                        </form>
                        {% endif %}
                        <form action="{{ url_for('delete_order', order_id=order.id) }}" method="POST" style="margin:0;">
                            <button type="submit" class="delete-btn">Xóa</button>
                        </form>
                    </div>
                </td>
            </tr>
            {% else %}
            <tr>
                <td colspan="10" class="empty-row">Hiện tại chưa có đơn đặt hàng nào được gửi lên hệ thống.</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def index():
  success = False
  if request.method == "POST":
    new_order = {
        "id": len(orders) + 1,
        "customer_name": request.form.get("customer_name"),
        "phone": request.form.get("phone"),
        "address": request.form.get("address"),
        "item_name": request.form.get("item_name"),
        "color": request.form.get("color"),
        "weight": float(request.form.get("weight", 0)),
        "total_price": float(request.form.get("weight", 0)) * 2000,
        "status": "Chưa làm",
    }
    orders.append(new_order)
    success = True
  return render_template_string(INDEX_HTML, success=success)


@app.route("/admin")
def admin():
  return render_template_string(ADMIN_HTML, orders=orders)


@app.route("/complete/<int:order_id>", methods=["POST"])
def complete_order(order_id):
  for order in orders:
    if order["id"] == order_id:
      order["status"] = "Đã giao"
  return redirect(url_for("admin"))


@app.route("/delete/<int:order_id>", methods=["POST"])
def delete_order(order_id):
  global orders
  orders = [order for order in orders if order["id"] != order_id]
  return redirect(url_for("admin"))


if __name__ == "__main__":
  app.run(debug=True)
    app.run(host='0.0.0.0', port=5000)
