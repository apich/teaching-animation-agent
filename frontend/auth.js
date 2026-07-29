/**
 * Auth modal for teaching animation website (xsyy.top style)
 * Self-contained: injects HTML/CSS on DOMContentLoaded
 */

const AUTH_API = '/api/auth';

/* ── Agreement texts ── */
const USER_AGREEMENT = `《用户协议》
版本号：v1.0.0
最后更新：2026-05-01

欢迎使用本服务。请您在注册、登录及使用服务前仔细阅读并理解本协议。

一、账号管理
1. 用户应妥善保管账号信息与登录凭证，并对账号下的一切操作承担责任。
2. 用户不得利用平台实施违法违规行为，不得发布侵犯他人合法权益的内容。
3. 用户有权申请注销账号。账号注销后，平台将按规则删除或匿名化您的个人数据，且该操作不可撤销。

二、使用规范
1. 用户应遵守中华人民共和国现行法律法规及公序良俗。
2. 用户不得通过技术手段干扰平台正常运行，不得恶意刷量、批量爬取或攻击系统。

三、内容与版权
1. 用户在平台生成或发布的内容，知识产权归用户所有。
2. 为实现产品运营与展示功能，用户授予平台在服务范围内的非独占展示与传播权。
3. 用户应确保其发布内容不侵犯第三方权益，如产生纠纷由用户自行承担责任。

四、免责声明
1. 平台将尽力保障服务稳定，但不承诺服务绝对不中断、无错误或完全满足特定需求。
2. 因不可抗力、网络故障、第三方服务异常等原因导致的损失，平台在法律允许范围内不承担间接损失责任。

五、协议变更与适用法律
1. 平台可根据业务发展对本协议进行更新，并通过适当方式提示。
2. 本协议的订立、执行与争议解决均适用中华人民共和国法律。`;

const PRIVACY_POLICY = `《隐私政策》
版本号：v1.0.0
最后更新：2026-05-01

本政策用于说明平台如何收集、使用、存储与保护您的个人信息。

一、我们收集的信息
1. 账号信息：用户名、手机号（如您提供）等。
2. 设备信息：设备标识、登录环境等，用于账号安全与设备绑定管理。
3. 使用记录：题目输入、生成记录、邀请记录、反馈信息、系统交互记录。

二、信息使用目的
1. 用于提供核心功能，包括登录认证、题目生成、次数管理、消息通知与问题反馈处理。
2. 用于产品优化与服务改进，包括故障排查、统计分析和体验优化。
3. 用于安全风控，防止欺诈、滥用和非法访问。

三、信息存储与保护
1. 我们采取合理措施保护您的信息安全，防止未经授权访问、泄露或篡改。
2. 在达到处理目的或您申请注销后，我们将依法删除或匿名化相关个人信息。

四、对外提供
1. 除法律法规要求或为提供服务所必需外，我们不会向无关第三方出售您的个人信息。
2. 在涉及第三方服务时，我们将要求其履行相应的信息保护义务。

五、您的权利
1. 您有权访问、更正、删除您的个人信息。
2. 您有权注销账号并要求删除相关个人数据（法律法规另有规定的除外）。

六、未成年人说明
若您为未成年人，请在监护人同意和指导下使用本服务。

七、法律适用
本政策受中华人民共和国法律管辖。`;

/* ── CSS injection ── */
function injectAuthStyles() {
  const style = document.createElement('style');
  style.textContent = `
/* Auth modal styles */
.auth-modal-overlay {
  display: none;
  position: fixed; inset: 0; z-index: 10000;
  background: rgba(0,0,0,0.45);
  backdrop-filter: blur(4px);
  -webkit-backdrop-filter: blur(4px);
  justify-content: center; align-items: center;
}
.auth-modal-overlay.active { display: flex; }

.auth-modal {
  background: #fff;
  border-radius: 16px;
  width: 420px; max-width: 92vw;
  max-height: 90vh; overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0,0,0,0.25);
  padding: 32px 28px 24px;
  position: relative;
  font-family: var(--font-sans, 'PingFang SC', 'Microsoft YaHei', sans-serif);
  color: var(--ink-black, #1a1a1a);
}
.auth-modal-close {
  position: absolute; top: 14px; right: 16px;
  background: none; border: none; font-size: 22px; cursor: pointer;
  color: var(--ink-grey, #999); line-height: 1;
}
.auth-modal-close:hover { color: var(--ink-black, #1a1a1a); }

.auth-tabs {
  display: flex; gap: 0; margin-bottom: 24px;
  border-bottom: 2px solid var(--border-color, #eee);
}
.auth-tab {
  flex: 1; text-align: center; padding: 10px 0; cursor: pointer;
  font-size: 15px; color: var(--ink-grey, #999);
  border-bottom: 2px solid transparent; margin-bottom: -2px;
  transition: color 0.2s, border-color 0.2s;
  background: none; border-top: none; border-left: none; border-right: none;
  font-family: inherit;
}
.auth-tab.active {
  color: var(--primary-red, #c0392b);
  border-bottom-color: var(--primary-red, #c0392b);
  font-weight: 600;
}

.auth-form { display: none; }
.auth-form.active { display: block; }

.auth-form h3 {
  font-size: 16px; margin: 0 0 18px; font-weight: 600;
  font-family: var(--font-serif, 'Noto Serif SC', serif);
}

.auth-field { margin-bottom: 14px; }
.auth-field label {
  display: block; font-size: 13px; color: var(--ink-grey, #666);
  margin-bottom: 5px;
}
.auth-field input {
  width: 100%; padding: 10px 12px; border: 1px solid var(--border-color, #ddd);
  border-radius: 10px; font-size: 14px; outline: none;
  font-family: inherit; box-sizing: border-box;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.auth-field input:focus {
  border-color: var(--primary-blue, #2980b9);
  box-shadow: 0 0 0 3px rgba(41,128,185,0.15);
}

.auth-field-inline {
  display: flex; gap: 10px;
}
.auth-field-inline input { flex: 1; }
.auth-field-inline button {
  white-space: nowrap; padding: 10px 16px; border-radius: 10px;
  border: 1px solid var(--primary-blue, #2980b9);
  background: #fff; color: var(--primary-blue, #2980b9);
  font-size: 13px; cursor: pointer; font-family: inherit;
}
.auth-field-inline button:hover { background: rgba(41,128,185,0.06); }

.auth-agreement {
  display: flex; align-items: flex-start; gap: 6px;
  font-size: 12px; color: var(--ink-grey, #888); margin: 14px 0;
}
.auth-agreement input[type="checkbox"] {
  margin-top: 2px; accent-color: var(--primary-red, #c0392b);
}
.auth-agreement a {
  color: var(--primary-blue, #2980b9); text-decoration: none;
}
.auth-agreement a:hover { text-decoration: underline; }

.auth-btn {
  width: 100%; padding: 12px; border: none; border-radius: 10px;
  background: var(--primary-red, #c0392b); color: #fff;
  font-size: 15px; font-weight: 600; cursor: pointer;
  font-family: inherit; transition: background 0.2s;
}
.auth-btn:hover { background: #a93226; }
.auth-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.auth-link-row {
  text-align: center; margin-top: 12px; font-size: 13px;
}
.auth-link-row a {
  color: var(--primary-blue, #2980b9); text-decoration: none; cursor: pointer;
}
.auth-link-row a:hover { text-decoration: underline; }

.auth-msg {
  font-size: 13px; margin-bottom: 10px; display: none;
  padding: 8px 10px; border-radius: 8px;
}
.auth-msg.error { display: block; color: var(--primary-red, #c0392b); background: #fdf0ef; }
.auth-msg.success { display: block; color: var(--jade-green, #27ae60); background: #eafaf1; }

/* 注册方式切换 */
.register-method-tabs {
  display: flex; gap: 0; margin-bottom: 20px;
  border-bottom: 2px solid var(--border-color, #E0DCD3);
}
.register-method-tab {
  flex: 1; padding: 10px 0; text-align: center;
  background: none; border: none; border-bottom: 2px solid transparent;
  margin-bottom: -2px; cursor: pointer; font-size: 14px;
  color: var(--ink-grey, #5A6A76); transition: all 0.2s;
}
.register-method-tab.active {
  color: var(--primary-red, #B83B43);
  border-bottom-color: var(--primary-red, #B83B43);
  font-weight: 500;
}
.register-method-tab:hover:not(.active) { color: var(--ink-black, #2B2B2B); }
.register-method-content { display: none; }
.register-method-content.active { display: block; }

/* 邀请码提示 */
.invite-hint {
  margin: 6px 0 0; font-size: 12px;
  color: var(--primary-red, #B83B43); line-height: 1.4;
}

/* 手机注册关闭提示 */
.phone-disabled-notice {
  text-align: center; padding: 16px 20px; margin-bottom: 20px;
  background: #fff3cd; border: 1px solid #ffc107; border-radius: 8px;
}
.phone-disabled-notice p {
  margin: 0; font-size: 14px; font-weight: 500;
  color: var(--ink-black, #2B2B2B);
}

/* Agreement modal */
.agreement-modal-overlay {
  display: none; position: fixed; inset: 0; z-index: 10001;
  background: rgba(0,0,0,0.5); justify-content: center; align-items: center;
}
.agreement-modal-overlay.active { display: flex; }
.agreement-modal {
  background: #fff; border-radius: 16px; width: 560px; max-width: 92vw;
  max-height: 80vh; overflow-y: auto; padding: 28px;
  box-shadow: 0 20px 60px rgba(0,0,0,0.3);
  white-space: pre-wrap; font-size: 14px; line-height: 1.8;
  color: var(--ink-black, #1a1a1a);
  font-family: var(--font-sans, 'PingFang SC', 'Microsoft YaHei', sans-serif);
}

/* Header user dropdown */
.auth-user-menu {
  position: relative; display: inline-block;
}
.auth-user-btn {
  display: inline-flex; align-items: center; gap: 6px;
  padding: 8px 16px; border-radius: 20px;
  background: var(--primary-red, #c0392b); color: #fff;
  border: none; font-size: 14px; cursor: pointer;
  font-family: inherit;
}
.auth-user-dropdown {
  display: none; position: absolute; right: 0; top: 100%;
  margin-top: 6px; background: #fff; border-radius: 10px;
  box-shadow: 0 6px 24px rgba(0,0,0,0.15); overflow: hidden;
  min-width: 120px; z-index: 9999;
}
.auth-user-dropdown a {
  display: block; padding: 10px 16px; font-size: 14px;
  color: var(--ink-black, #1a1a1a); text-decoration: none;
  cursor: pointer;
}
.auth-user-dropdown a:hover { background: #f5f5f5; }
`;
  document.head.appendChild(style);
}

/* ── HTML injection ── */
function injectAuthHTML() {
  const div = document.createElement('div');
  div.innerHTML = `
<!-- Auth Modal -->
<div id="authModalOverlay" class="auth-modal-overlay" onclick="if(event.target===this)hideLoginModal()">
  <div class="auth-modal">
    <button class="auth-modal-close" onclick="hideLoginModal()">&times;</button>

    <div class="auth-tabs">
      <button class="auth-tab active" data-tab="login" onclick="switchTab('login')">登录</button>
      <button class="auth-tab" data-tab="register" onclick="switchTab('register')">注册</button>
    </div>

    <!-- Login Form -->
    <div id="auth-login" class="auth-form active">
      <div id="loginMsg" class="auth-msg"></div>
      <form onsubmit="return handleLogin(event)">
        <div class="auth-field">
          <label>用户名</label>
          <input type="text" id="loginUsername" placeholder="请输入用户名" required>
        </div>
        <div class="auth-field">
          <label>密码</label>
          <input type="password" id="loginPassword" placeholder="请输入密码" required>
        </div>
        <div class="auth-agreement">
          <input type="checkbox" id="loginAgree">
          <span>我已阅读并同意 <a href="javascript:void(0)" onclick="openAgreementModal('user')">《用户协议》</a> 和 <a href="javascript:void(0)" onclick="openAgreementModal('privacy')">《隐私政策》</a></span>
        </div>
        <button type="submit" class="auth-btn">登录</button>
      </form>
      <div class="auth-link-row">
        <a href="javascript:void(0)" onclick="switchTab('forgot')">忘记密码？</a>
      </div>
    </div>

    <!-- Register Form -->
    <div id="auth-register" class="auth-form">
      <div id="registerMsg" class="auth-msg"></div>

      <!-- 注册方式切换 -->
      <div class="register-method-tabs">
        <button type="button" class="register-method-tab active" onclick="switchRegisterMethod('password')">用户名密码</button>
        <button type="button" class="register-method-tab" onclick="switchRegisterMethod('phone')">手机验证码</button>
      </div>

      <!-- 用户名密码注册 -->
      <div id="registerPasswordForm" class="register-method-content active">
        <form onsubmit="return handleRegister(event)">
          <div class="auth-field">
            <label>用户名</label>
            <input type="text" id="regUsername" placeholder="请输入用户名" required>
          </div>
          <div class="auth-field">
            <label>密码</label>
            <input type="password" id="regPassword" placeholder="请输入密码" required minlength="6">
          </div>
          <div class="auth-field">
            <label>确认密码</label>
            <input type="password" id="regPasswordConfirm" placeholder="请再次输入密码" required minlength="6">
          </div>
          <div class="auth-field">
            <label>邀请码</label>
            <input type="text" id="regInviteCode" placeholder="请输入邀请码" required>
            <p class="invite-hint">可选官方邀请码：XSYY2026</p>
          </div>
          <div class="auth-agreement">
            <input type="checkbox" id="regAgree">
            <span>我已阅读并同意 <a href="javascript:void(0)" onclick="openAgreementModal('user')">《用户协议》</a> 和 <a href="javascript:void(0)" onclick="openAgreementModal('privacy')">《隐私政策》</a></span>
          </div>
          <button type="submit" class="auth-btn">注册</button>
        </form>
      </div>

      <!-- 手机验证码注册（已关闭） -->
      <div id="registerPhoneForm" class="register-method-content">
        <div class="phone-disabled-notice">
          <p>⚠️ 该功能暂时关闭，请通过用户名密码和邀请码注册</p>
        </div>
        <form onsubmit="event.preventDefault(); return false;">
          <div class="auth-field">
            <label>手机号</label>
            <div class="auth-field-inline">
              <input type="tel" id="regPhone" placeholder="11位手机号" disabled style="flex:1;opacity:0.5;">
              <button type="button" class="auth-btn-inline" disabled style="opacity:0.5;cursor:not-allowed;">发送验证码</button>
            </div>
          </div>
          <div class="auth-field">
            <label>验证码</label>
            <input type="text" placeholder="6位验证码" maxlength="6" disabled style="opacity:0.5;">
          </div>
          <div class="auth-agreement" style="opacity:0.5;">
            <input type="checkbox" disabled>
            <span>我已阅读并同意 <a href="javascript:void(0)" onclick="openAgreementModal('user')">《用户协议》</a> 和 <a href="javascript:void(0)" onclick="openAgreementModal('privacy')">《隐私政策》</a></span>
          </div>
          <button type="submit" class="auth-btn" disabled style="opacity:0.5;cursor:not-allowed;">注册</button>
        </form>
      </div>
    </div>

    <!-- Forgot Password Form -->
    <div id="auth-forgot" class="auth-form">
      <h3>找回密码</h3>
      <div id="forgotMsg" class="auth-msg"></div>
      <form onsubmit="return handleForgotPassword(event)">
        <div class="auth-field">
          <label>手机号</label>
          <div class="auth-field-inline">
            <input type="text" id="forgotPhone" placeholder="请输入手机号" required>
            <button type="button" onclick="sendVerificationCode()">发送验证码</button>
          </div>
        </div>
        <div class="auth-field">
          <label>验证码</label>
          <input type="text" id="forgotCode" placeholder="请输入验证码" required>
        </div>
        <div class="auth-field">
          <label>新密码</label>
          <input type="password" id="forgotNewPwd" placeholder="请输入新密码" required>
        </div>
        <div class="auth-field">
          <label>确认新密码</label>
          <input type="password" id="forgotNewPwdConfirm" placeholder="请再次输入新密码" required>
        </div>
        <button type="submit" class="auth-btn">重置密码</button>
      </form>
      <div class="auth-link-row">
        <a href="javascript:void(0)" onclick="switchTab('login')">返回登录</a>
      </div>
    </div>
  </div>
</div>

<!-- Agreement Modal -->
<div id="agreementModalOverlay" class="agreement-modal-overlay" onclick="if(event.target===this)this.classList.remove('active')">
  <div class="agreement-modal" id="agreementContent"></div>
</div>
`;
  document.body.appendChild(div);
}

/* ── Public API ── */

function initAuthModal() {
  injectAuthStyles();
  injectAuthHTML();
  checkAuth();
}

function showLoginModal() {
  document.getElementById('authModalOverlay').classList.add('active');
  switchTab('login');
}

function hideLoginModal() {
  document.getElementById('authModalOverlay').classList.remove('active');
  clearMessages();
}

function switchTab(tabName) {
  // Update tabs
  document.querySelectorAll('.auth-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.tab === tabName);
  });
  // Update forms
  document.querySelectorAll('.auth-form').forEach(f => f.classList.remove('active'));
  const el = document.getElementById('auth-' + tabName);
  if (el) el.classList.add('active');
  clearMessages();
}

function switchRegisterMethod(method) {
  // 切换标签样式
  document.querySelectorAll('.register-method-tab').forEach((tab, i) => {
    tab.classList.toggle('active', (method === 'password' && i === 0) || (method === 'phone' && i === 1));
  });
  // 切换表单显示
  const pwdForm = document.getElementById('registerPasswordForm');
  const phoneForm = document.getElementById('registerPhoneForm');
  if (pwdForm) pwdForm.classList.toggle('active', method === 'password');
  if (phoneForm) phoneForm.classList.toggle('active', method === 'phone');
  clearMessages();
}

function handleLogin(e) {
  e.preventDefault();
  const msg = document.getElementById('loginMsg');
  const username = document.getElementById('loginUsername').value.trim();
  const password = document.getElementById('loginPassword').value;
  const agreed = document.getElementById('loginAgree').checked;

  if (!agreed) { showMsg(msg, '请先同意用户协议和隐私政策', 'error'); return false; }
  if (!username || !password) { showMsg(msg, '请填写用户名和密码', 'error'); return false; }

  fetch(AUTH_API + '/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
  })
    .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.detail || '登录失败')))
    .then(data => {
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      hideLoginModal();
      checkAuth();
    })
    .catch(err => showMsg(msg, typeof err === 'string' ? err : '登录失败', 'error'));
  return false;
}

function handleRegister(e) {
  e.preventDefault();
  const msg = document.getElementById('registerMsg');
  const username = document.getElementById('regUsername').value.trim();
  const password = document.getElementById('regPassword').value;
  const confirm = document.getElementById('regPasswordConfirm').value;
  const inviteCode = document.getElementById('regInviteCode').value.trim();
  const agreed = document.getElementById('regAgree').checked;

  if (!agreed) { showMsg(msg, '请先同意用户协议和隐私政策', 'error'); return false; }
  if (password !== confirm) { showMsg(msg, '两次密码不一致', 'error'); return false; }
  if (!username || !password || !inviteCode) { showMsg(msg, '请填写所有字段', 'error'); return false; }

  fetch(AUTH_API + '/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password, invite_code: inviteCode })
  })
    .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.detail || '注册失败')))
    .then(data => {
      localStorage.setItem('auth_token', data.token);
      localStorage.setItem('auth_user', JSON.stringify(data.user));
      hideLoginModal();
      checkAuth();
    })
    .catch(err => showMsg(msg, typeof err === 'string' ? err : '注册失败', 'error'));
  return false;
}

function sendVerificationCode() {
  const phone = document.getElementById('forgotPhone').value.trim();
  const msg = document.getElementById('forgotMsg');
  if (!phone) { showMsg(msg, '请输入手机号', 'error'); return; }

  fetch(AUTH_API + '/send-code', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone })
  })
    .then(r => r.json())
    .then(data => {
      showMsg(msg, '验证码已发送（测试模式：' + data.code + '）', 'success');
    })
    .catch(() => showMsg(msg, '发送失败', 'error'));
}

function handleForgotPassword(e) {
  e.preventDefault();
  const msg = document.getElementById('forgotMsg');
  const phone = document.getElementById('forgotPhone').value.trim();
  const code = document.getElementById('forgotCode').value.trim();
  const newPwd = document.getElementById('forgotNewPwd').value;
  const newPwdConfirm = document.getElementById('forgotNewPwdConfirm').value;

  if (newPwd !== newPwdConfirm) { showMsg(msg, '两次密码不一致', 'error'); return false; }
  if (!phone || !code || !newPwd) { showMsg(msg, '请填写所有字段', 'error'); return false; }

  fetch(AUTH_API + '/reset-password', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ phone, code, new_password: newPwd })
  })
    .then(r => r.ok ? r.json() : r.json().then(j => Promise.reject(j.detail || '重置失败')))
    .then(() => {
      showMsg(msg, '密码重置成功，请登录', 'success');
      setTimeout(() => switchTab('login'), 1500);
    })
    .catch(err => showMsg(msg, typeof err === 'string' ? err : '重置失败', 'error'));
  return false;
}

function openAgreementModal(type) {
  const el = document.getElementById('agreementContent');
  el.textContent = type === 'privacy' ? PRIVACY_POLICY : USER_AGREEMENT;
  document.getElementById('agreementModalOverlay').classList.add('active');
}

function logout() {
  localStorage.removeItem('auth_token');
  localStorage.removeItem('auth_user');
  checkAuth();
}

function checkAuth() {
  const token = localStorage.getItem('auth_token');
  const userStr = localStorage.getItem('auth_user');
  // Find the login button in the header
  const loginBtn = document.getElementById('loginLink') ||
    document.querySelector('[onclick*="showLoginModal()"]');

  if (!loginBtn) return;

  if (token && userStr) {
    const user = JSON.parse(userStr);
    // Replace button with user menu
    loginBtn.outerHTML = `
      <div class="auth-user-menu">
        <button class="auth-user-btn" onclick="this.nextElementSibling.style.display=this.nextElementSibling.style.display==='block'?'none':'block'">
          ${escapeHtmlSafe(user.username)} ▾
        </button>
        <div class="auth-user-dropdown">
          <a href="javascript:void(0)" onclick="logout()">退出登录</a>
        </div>
      </div>`;
    // Close dropdown on outside click
    document.addEventListener('click', function closeDropdown(ev) {
      const menu = document.querySelector('.auth-user-menu');
      if (menu && !menu.contains(ev.target)) {
        const dd = menu.querySelector('.auth-user-dropdown');
        if (dd) dd.style.display = 'none';
      }
    });
  } else {
    // If currently showing user menu, restore login button
    const menu = document.querySelector('.auth-user-menu');
    if (menu) {
      menu.outerHTML = `<a href="#" class="nav-link top-action-btn top-action-login" id="loginLink" onclick="showLoginModal(); return false;">
        <span class="btn-glow"></span>
        <span class="btn-shine"></span>
        <span class="btn-text">登入</span>
      </a>`;
    }
  }
}

/* ── Helpers ── */

function showMsg(el, text, type) {
  el.className = 'auth-msg ' + type;
  el.textContent = text;
}

function clearMessages() {
  document.querySelectorAll('.auth-msg').forEach(m => {
    m.className = 'auth-msg';
    m.textContent = '';
  });
}

function escapeHtmlSafe(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

/* ── Auto-init ── */
document.addEventListener('DOMContentLoaded', initAuthModal);
