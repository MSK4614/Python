from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, g
from utils.data_utils import load_partners, add_partner, get_partner_by_id, update_partner_status, delete_partner

app = Flask(__name__)
app.secret_key = 'xundazi-dev-key'  # 用于flash消息

# 2. 详情页路由
@app.route('/detail/<partner_id>')
def detail(partner_id):
    partner = get_partner_by_id(partner_id)
    if not partner:
        # 找不到时返回标准的 404 页面
        abort(404)
    return render_template('detail.html', partner=partner)

# 3. 首页路由
@app.route('/')
def index():
    category = request.args.get('category', '全部')
    keyword = request.args.get('keyword', '').strip()  # 获取搜索关键词
    partners = load_partners()
    
    # 先按分类筛选
    filtered = partners if category == '全部' else [p for p in partners if p['category'] == category]
    
    # 再按关键词过滤（同时匹配标题、地点、描述）
    if keyword:
        filtered = [
            p for p in filtered 
            if keyword in p.get('title', '') 
            or keyword in p.get('location', '') 
            or keyword in p.get('description', '')
        ]
        
    return render_template('index.html', partners=filtered, current_category=category, keyword=keyword)

# 4. 发布页路由
@app.route('/publish', methods=['GET', 'POST'])
def publish():
    if request.method == 'POST':
        # 获取表单数据
        new_partner = {
            "title": request.form.get('title'),
            "location": request.form.get('location'),
            "time": request.form.get('time'),
            "category": request.form.get('category'),
            "description": request.form.get('description')
        }

        # 基础校验：如果有任何一个字段为空
        if not all(new_partner.values()):
            flash('所有字段均为必填项！', 'danger')
            return render_template('publish.html')

        # 保存数据
        add_partner(new_partner)
        flash('搭子发布成功！', 'success')
        return redirect(url_for('index'))

    # GET 请求直接显示空表单
    return render_template('publish.html')

# 【V2新增】修改状态路由
@app.route('/update_status/<partner_id>', methods=['POST'])
def update_status(partner_id):
    new_status = request.form.get('status')
    # 安全校验：只允许修改为这三种状态
    if new_status in ['招募中', '已满员', '已结束']:
        update_partner_status(partner_id, new_status)
        flash(f'状态已更新为：{new_status}', 'success')
    return redirect(url_for('detail', partner_id=partner_id))

# 【V2新增】管理员入口与口令验证
ADMIN_PASSWORD = 'admin2026'

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['admin'] = True
            return redirect(url_for('admin'))
        else:
            flash('口令错误！', 'danger')

  
    # 只有当用户真正登录了，才把 g.is_admin_mode 设为 True
    # 这样只有在这个路由下渲染的模板才会显示管理功能
    if session.get('admin'):
        g.is_admin_mode = True
    else:
        g.is_admin_mode = False

    partners = load_partners()
    return render_template('admin.html', partners=partners)

# 【V2新增】删除帖子路由 (需管理员权限)
@app.route('/delete/<partner_id>')
def delete(partner_id):
    if not session.get('admin'):
        abort(403) # 权限不足，返回 403 Forbidden
    delete_partner(partner_id)
    flash('帖子已删除！', 'success')
    return redirect(url_for('admin'))

# 5. 启动入口
if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)