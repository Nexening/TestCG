# Android-safe 修正版 main.py
# 目标：解决 APK 灰黑屏（深色模式）问题
# 核心修复点：ThemeMode / ft.colors / client_storage 生命周期 / overlay 安全

import flet as ft
import re
import datetime
import json
import shutil
import os
from pathlib import Path


def main(page: ft.Page):
    # =========================
    # 0. Page 基础设置（Android-safe）
    # =========================
    page.title = "My Omnis"
    page.padding = 0
    page.theme_mode = ft.ThemeMode.SYSTEM  # ★ 必须用枚举

    # -------------------------
    # 延迟初始化的偏好（必须）
    # -------------------------
    icon_preference = ["star"]
    sort_preference = ["desc"]

    def on_ready(e):
        # client_storage 只能在 on_ready 之后安全访问
        icon_preference[0] = page.client_storage.get("icon_preference") or "star"
        sort_preference[0] = page.client_storage.get("sort_preference") or "desc"
        page.update()

    page.on_ready = on_ready

    # =========================
    # 1. 颜色系统（严禁字符串颜色）
    # =========================
    def get_app_colors():
        is_dark = page.theme_mode == ft.ThemeMode.DARK
        return {
            "bg": ft.colors.GREY_900 if is_dark else ft.colors.GREY_100,
            "card": ft.colors.GREY_800 if is_dark else ft.colors.WHITE,
            "text": ft.colors.WHITE if is_dark else ft.colors.BLACK,
            "sub_text": ft.colors.GREY_400 if is_dark else ft.colors.GREY_700,
            "icon": ft.colors.WHITE if is_dark else ft.colors.GREY_700,
            "divider": ft.colors.GREY_700 if is_dark else ft.colors.GREY_300,
            "input_bg": ft.colors.GREY_900 if is_dark else ft.colors.WHITE,
            "orange": ft.colors.ORANGE_400 if is_dark else ft.colors.ORANGE_600,
            "blue": ft.colors.BLUE_400 if is_dark else ft.colors.BLUE_600,
            "shadow": ft.colors.BLACK if is_dark else ft.colors.BLACK12,
        }

    page.bgcolor = get_app_colors()["bg"]

    # =========================
    # 2. Storage 工具函数
    # =========================
    def get_all_logs():
        data = page.client_storage.get("tuntun_logs")
        if not data:
            return []
        return json.loads(data) if isinstance(data, str) else data

    def save_logs(logs):
        page.client_storage.set("tuntun_logs", json.dumps(logs, ensure_ascii=False))

    # =========================
    # 3. 日志页（精简但安全）
    # =========================
    def get_log_view():
        colors = get_app_colors()

        log_list = ft.Column(expand=True, spacing=10)

        def refresh():
            log_list.controls.clear()
            logs = get_all_logs()
            logs.sort(key=lambda x: x.get("id", 0), reverse=(sort_preference[0] == "desc"))

            if not logs:
                log_list.controls.append(
                    ft.Text("暂无记录", color=colors["sub_text"])
                )
            else:
                for item in logs:
                    log_list.controls.append(
                        ft.Container(
                            padding=12,
                            bgcolor=colors["card"],
                            border_radius=12,
                            shadow=ft.BoxShadow(blur_radius=4, color=colors["shadow"]),
                            content=ft.Column([
                                ft.Text(item.get("date_str", ""), color=colors["blue"], weight="bold"),
                                ft.Text("；".join(item.get("events", [])), color=colors["text"])
                            ])
                        )
                    )
            log_list.update()

        refresh()

        return ft.Column(expand=True, controls=[
            ft.Container(height=40),
            ft.Text("日志", size=22, weight="bold", color=colors["text"]),
            log_list
        ])

    # =========================
    # 4. 设置页（仅保留关键功能）
    # =========================
    def get_settings_view():
        colors = get_app_colors()

        def toggle_theme(e):
            page.theme_mode = ft.ThemeMode.DARK if e.control.value else ft.ThemeMode.LIGHT
            page.bgcolor = get_app_colors()["bg"]
            page.update()

        return ft.Column(expand=True, controls=[
            ft.Container(height=40),
            ft.Text("设置", size=22, weight="bold", color=colors["text"]),
            ft.Switch(
                label="暗黑模式",
                value=(page.theme_mode == ft.ThemeMode.DARK),
                on_change=toggle_theme,
                active_color=colors["orange"],
            )
        ])

    # =========================
    # 5. NavigationBar（Android-safe）
    # =========================
    def on_nav_change(e):
        page.clean()
        idx = e.control.selected_index
        if idx == 0:
            page.add(get_log_view())
        else:
            page.add(get_settings_view())
        page.update()

    page.navigation_bar = ft.NavigationBar(
        selected_index=0,
        bgcolor=get_app_colors()["card"],
        on_change=on_nav_change,
        destinations=[
            ft.NavigationDestination(icon="pets", label="日志"),
            ft.NavigationDestination(icon="settings", label="设置"),
        ]
    )

    page.add(get_log_view())


if __name__ == "__main__":
    ft.app(target=main, assets_dir=".")
