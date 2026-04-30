#!/usr/bin/env python3
"""
Feishu Image Uploader for db-query skill.

通过飞书 Open API 上传图片并发送到聊天窗口。
无需 sharp/Node.js 依赖，纯 Python + requests。

用法:
    from feishu_uploader import FeishuUploader
    
    uploader = FeishuUploader()
    image_key = uploader.upload("chart.png")
    uploader.send_image_to_chat("oc_xxxxxx", image_key)
    uploader.reply_with_image("om_xxxxxx", image_key)
"""

import json
import os
import sys
import time
import urllib.request
import urllib.parse

# ── 路径常量 ──────────────────────────────────────────────
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.expanduser("~/.openclaw/openclaw.json")

# 可选：通过环境变量覆盖（技能.env）
ENV_APP_ID = os.environ.get("FEISHU_APP_ID")
ENV_APP_SECRET = os.environ.get("FEISHU_APP_SECRET")


class FeishuUploader:
    """飞书图片上传 + 发送工具"""

    def __init__(self, app_id=None, app_secret=None):
        self.app_id = app_id or ENV_APP_ID or self._load_app_id()
        self.app_secret = app_secret or ENV_APP_SECRET or self._load_app_secret()
        self._token = None
        self._token_expires_at = 0

    # ── 凭据读取 ────────────────────────────────────────

    def _load_openclaw_config(self):
        """从 openclaw.json 读取飞书渠道配置"""
        if not os.path.exists(CONFIG_PATH):
            raise RuntimeError(
                f"找不到 OpenClaw 配置文件: {CONFIG_PATH}\n"
                f"请确保 openclaw.json 中存在 channels.feishu 配置"
            )
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        feishu = cfg.get("channels", {}).get("feishu", {})
        return feishu

    def _load_app_id(self):
        config = self._load_openclaw_config()
        app_id = config.get("appId")
        if not app_id:
            raise RuntimeError(
                "未找到飞书 App ID。\n"
                "请在 openclaw.json 的 channels.feishu 中配置 appId，\n"
                "或设置环境变量 FEISHU_APP_ID"
            )
        return app_id

    def _load_app_secret(self):
        config = self._load_openclaw_config()
        app_secret = config.get("appSecret")
        if not app_secret:
            raise RuntimeError(
                "未找到飞书 App Secret。\n"
                "请在 openclaw.json 的 channels.feishu 中配置 appSecret，\n"
                "或设置环境变量 FEISHU_APP_SECRET"
            )
        return app_secret

    # ── Token 管理 ─────────────────────────────────────

    def _get_tenant_token(self):
        """获取 tenant_access_token（带缓存）"""
        now = time.time()
        if self._token and now < self._token_expires_at - 60:
            return self._token

        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        body = json.dumps({
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }).encode("utf-8")

        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("code") != 0:
                    raise RuntimeError(f"获取 token 失败: {data.get('msg', 'unknown error')}")
                self._token = data["tenant_access_token"]
                self._token_expires_at = now + data.get("expire", 7200)
                return self._token
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Feishu API HTTP {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Feishu API 网络错误: {e.reason}") from e

    # ── 图片上传 ─────────────────────────────────────────

    def upload(self, image_path: str, image_type: str = "message") -> str:
        """
        上传图片到飞书，返回 image_key。

        Args:
            image_path: 本地图片文件路径
            image_type: "message"（聊天消息）或 "avatar"（头像）

        Returns:
            image_key: 飞书图片 key，可用于后续发送

        Raises:
            FileNotFoundError: 图片文件不存在
            RuntimeError: 上传失败
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"图片文件不存在: {image_path}")

        token = self._get_tenant_token()
        boundary = "----FormBoundary" + os.urandom(16).hex()
        filename = os.path.basename(image_path)

        # 构建 multipart/form-data
        with open(image_path, "rb") as f:
            file_data = f.read()

        body_parts = []
        body_parts.append(f"--{boundary}\r\n")
        body_parts.append(f'Content-Disposition: form-data; name="image_type"\r\n\r\n')
        body_parts.append(f"{image_type}\r\n")
        body_parts.append(f"--{boundary}\r\n")
        body_parts.append(f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n')
        body_parts.append("Content-Type: image/png\r\n\r\n")
        body_data = "".join(body_parts).encode("utf-8") + file_data + f"\r\n--{boundary}--\r\n".encode("utf-8")

        url = "https://open.feishu.cn/open-apis/im/v1/images"
        req = urllib.request.Request(url, data=body_data, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")

        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("code") != 0:
                    raise RuntimeError(f"图片上传失败: {data.get('msg', 'unknown error')}")
                return data["data"]["image_key"]
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"Feishu API HTTP {e.code}: {e.reason}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"Feishu API 网络错误: {e.reason}") from e

    # ── 图片发送 ─────────────────────────────────────────

    def send_image_to_chat(self, chat_id: str, image_key: str) -> dict:
        """
        向指定会话发送图片消息。

        Args:
            chat_id: 飞书会话 ID（如 "oc_xxxxxxxx"）
            image_key: 通过 upload() 获取的图片 key

        Returns:
            API 响应 JSON（解析后）
        """
        token = self._get_tenant_token()
        content = json.dumps({"image_key": image_key})
        body = json.dumps({
            "receive_id": chat_id,
            "msg_type": "image",
            "content": content,
        }).encode("utf-8")

        url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"发送图片失败 HTTP {e.code}: {e.reason}") from e

    def reply_with_image(self, message_id: str, image_key: str) -> dict:
        """
        回复指定消息，发送图片。

        Args:
            message_id: 要回复的消息 ID（如 "om_xxxxxxxx"）
            image_key: 通过 upload() 获取的图片 key

        Returns:
            API 响应 JSON（解析后）
        """
        token = self._get_tenant_token()
        content = json.dumps({"image_key": image_key})
        body = json.dumps({
            "content": content,
            "msg_type": "image",
        }).encode("utf-8")

        url = f"https://open.feishu.cn/open-apis/im/v1/messages/{message_id}/reply"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")

        try:
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"回复图片失败 HTTP {e.code}: {e.reason}") from e

    # ── 批量快捷操作 ─────────────────────────────────────

    def upload_and_send(self, image_path: str, target: str, is_message_id: bool = True) -> str:
        """
        上传并发送图片，一步到位。

        Args:
            image_path: 本地图片文件路径
            target: 消息 ID（reply）或会话 ID（send）
            is_message_id: True=回复消息, False=发送到会话

        Returns:
            image_key
        """
        image_key = self.upload(image_path)
        if is_message_id:
            self.reply_with_image(target, image_key)
            print(f"✅ 已回复消息 {target} 并发送图片: {image_path}", file=sys.stderr)
        else:
            self.send_image_to_chat(target, image_key)
            print(f"✅ 已发送图片到会话 {target}: {image_path}", file=sys.stderr)
        return image_key

    def upload_batch(self, image_paths: list, target: str, is_message_id: bool = True) -> list:
        """
        批量上传并发送多张图片。

        Args:
            image_paths: 图片路径列表
            target: 消息 ID 或会话 ID
            is_message_id: True=回复消息, False=发送到会话

        Returns:
            image_key 列表
        """
        keys = []
        for path in image_paths:
            key = self.upload_and_send(path, target, is_message_id)
            keys.append(key)
        return keys


# ── CLI 用法 ──────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="飞书图片上传工具")
    parser.add_argument("image", nargs="+", help="图片文件路径")
    parser.add_argument("--to-chat", help="发送到指定会话 (chat_id)")
    parser.add_argument("--reply", help="回复指定消息 (message_id)")
    parser.add_argument("--app-id", help="飞书 App ID（默认从 openclaw.json 读取）")
    parser.add_argument("--app-secret", help="飞书 App Secret（默认从 openclaw.json 读取）")

    args = parser.parse_args()

    try:
        uploader = FeishuUploader(app_id=args.app_id, app_secret=args.app_secret)

        for img_path in args.image:
            key = uploader.upload(img_path)
            print(f"image_key: {key}")

            if args.reply:
                uploader.reply_with_image(args.reply, key)
                print(f"  → 已回复 {args.reply}")
            elif args.to_chat:
                uploader.send_image_to_chat(args.to_chat, key)
                print(f"  → 已发送到 {args.to_chat}")

    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        sys.exit(1)
